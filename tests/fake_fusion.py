"""
A small Fusion stand-in that reproduces the behaviours we verified against
DaVinci Resolve 21, so compiler tests exercise REAL animation semantics:

* SetInput(name, value, time) on an input WITHOUT a spline just sets a static
  value (the time is ignored) - the bug that made old templates never animate;
* AddModifier(input, "BezierSpline") seeds one key at the comp's current time
  holding the old value; SetKeyFrames(..., replace=True) does not remove it;
* DeleteKeyFrames never removes a spline's last remaining key;
* Bezier handles are stored RELATIVE to their key;
* "XYPath" connects splines to both X and Y and ignores plain SetInput on them.
"""


def _bezier(p0, p1, p2, p3, u):
    a = 1.0 - u
    return a * a * a * p0 + 3 * a * a * u * p1 + 3 * a * u * u * p2 + u * u * u * p3


class FakeSpline:
    def __init__(self, seed_time, seed_value):
        self.keys = {float(seed_time): {1: float(seed_value)}}

    def SetKeyFrames(self, table, replace=False):
        for t, k in table.items():
            self.keys[float(t)] = dict(k)

    def GetKeyFrames(self):
        return {t: dict(k) for t, k in self.keys.items()}

    def DeleteKeyFrames(self, start, end=None):
        end = start if end is None else end
        doomed = [t for t in self.keys if start <= t <= end]
        if len(doomed) >= len(self.keys):
            doomed = doomed[:-1] if doomed else []
        for t in doomed:
            del self.keys[t]

    def value(self, t):
        times = sorted(self.keys)
        if t <= times[0]:
            return self.keys[times[0]][1]
        if t >= times[-1]:
            return self.keys[times[-1]][1]
        for t0, t1 in zip(times, times[1:]):
            if t0 <= t <= t1:
                k0, k1 = self.keys[t0], self.keys[t1]
                v0, v1 = k0[1], k1[1]
                rh = k0.get("RH", {1: (t1 - t0) / 3.0, 2: (v1 - v0) / 3.0})
                lh = k1.get("LH", {1: -(t1 - t0) / 3.0, 2: -(v1 - v0) / 3.0})
                x = (t0, t0 + rh[1], t1 + lh[1], t1)
                y = (v0, v0 + rh[2], v1 + lh[2], v1)
                lo, hi = 0.0, 1.0
                for _ in range(50):
                    mid = (lo + hi) / 2
                    if _bezier(*x, mid) < t:
                        lo = mid
                    else:
                        hi = mid
                return _bezier(*y, (lo + hi) / 2)
        return self.keys[times[-1]][1]

    def GetTool(self):
        return self


class FakeOutput:
    def __init__(self, tool):
        self.tool = tool

    def GetTool(self):
        return self.tool


class FakeInputRef:
    def __init__(self, tool, name):
        self.tool, self.name = tool, name

    def ConnectTo(self, output):
        self.tool.connections[self.name] = output

    def GetConnectedOutput(self):
        mod = self.tool.modifiers.get(self.name)
        return FakeOutput(mod) if mod is not None else None

    def SetExpression(self, expr):
        self.tool.expressions[self.name] = expr


class FakeTool:
    def __init__(self, comp, regid, name):
        object.__setattr__(self, "comp", comp)
        object.__setattr__(self, "regid", regid)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "static", {})
        object.__setattr__(self, "modifiers", {})
        object.__setattr__(self, "connections", {})
        object.__setattr__(self, "expressions", {})
        object.__setattr__(self, "Output", FakeOutput(self))
        object.__setattr__(self, "Mask", FakeOutput(self))

    # --- Fusion API -----------------------------------------------------
    def SetAttrs(self, attrs):
        new = attrs.get("TOOLS_Name")
        if new:
            self.comp.tools.pop(self.name, None)
            object.__setattr__(self, "name", new)
            self.comp.tools[new] = self

    def GetAttrs(self):
        return {"TOOLS_Name": self.name, "TOOLS_RegID": self.regid}

    def Delete(self):
        self.comp.tools.pop(self.name, None)

    def AddModifier(self, input_name, kind):
        seed = self.static.get(input_name, 0.0)
        if kind == "XYPath":
            if not isinstance(seed, (list, tuple)):
                seed = [0.5, 0.5]
            path = FakeTool(self.comp, "XYPath", f"{self.name}_{input_name}Path")
            path.modifiers["X"] = FakeSpline(self.comp.current_time, seed[0])
            path.modifiers["Y"] = FakeSpline(self.comp.current_time, seed[1])
            self.modifiers[input_name] = path
        elif kind == "BezierSpline":
            self.modifiers[input_name] = FakeSpline(self.comp.current_time, seed if not isinstance(seed, (list, tuple)) else 0.0)
        else:  # tool-like modifiers, e.g. the Text+ Follower (StyledTextFollower)
            self.modifiers[input_name] = FakeTool(self.comp, kind, f"{self.name}_{kind}")
        return True

    def SetInput(self, name, value, time=None):
        mod = self.modifiers.get(name)
        if mod is None:
            self.static[name] = value          # time ignored: no spline => static
        elif isinstance(mod, FakeSpline) and time is not None:
            mod.SetKeyFrames({float(time): {1: float(value)}})
        # animated input without a time / XYPath axis: ignored, like Resolve

    def GetInput(self, name, time=0.0):
        mod = self.modifiers.get(name)
        if isinstance(mod, FakeSpline):
            return mod.value(float(time))
        if isinstance(mod, FakeTool) and mod.regid == "XYPath":
            return [mod.GetInput("X", time), mod.GetInput("Y", time)]
        if isinstance(mod, FakeTool):
            return self.static.get(name)
        return self.static.get(name)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return FakeInputRef(self, name)


class FakeComp:
    def __init__(self, render_start=0, render_end=71):
        self.tools = {}
        self.current_time = float(render_start)
        self.attrs = {"COMPN_RenderStart": float(render_start), "COMPN_RenderEnd": float(render_end)}
        self._n = 0
        for regid, name in (("TextPlus", "Template"), ("MediaOut", "MediaOut1")):
            self.tools[name] = FakeTool(self, regid, name)

    def AddTool(self, regid, x=0, y=0):
        self._n += 1
        t = FakeTool(self, regid, f"{regid}{self._n}")
        self.tools[t.name] = t
        return t

    def FindTool(self, name):
        return self.tools.get(name)

    def GetToolList(self, selected=False):
        return {i: t for i, t in enumerate(list(self.tools.values()), start=1)}

    def GetAttrs(self):
        return dict(self.attrs)

    def Lock(self):
        pass

    def Unlock(self):
        pass

    def StartUndo(self, name):
        pass

    def EndUndo(self, keep=True):
        pass


class FakeItem:
    def __init__(self, comp, duration):
        self.comp, self.duration = comp, duration

    def GetFusionCompCount(self):
        return 1

    def GetFusionCompByIndex(self, i):
        return self.comp

    def GetDuration(self):
        return self.duration


class FakeBridge:
    def __init__(self, fps=24.0, res=(1920, 1080)):
        self.fps, self.res = fps, res

    def get_timeline_fps(self):
        return self.fps

    def get_timeline_resolution(self):
        return self.res


def make_item(frames=72, render_start=0, res=(1920, 1080), fps=24.0):
    comp = FakeComp(render_start, render_start + frames - 1)
    return FakeItem(comp, frames), comp, FakeBridge(fps, res)
