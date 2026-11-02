"""
CaptionForge for Resolve - Subtitle & Word Timing Parser
Handles timeline subtitle tracks, transcription cues, word-per-slide grouping,
punctuation stripping, and word rearrangement between lines and caption groups.
"""

import re
import os

class SubtitleCue:
    """Represents a single timed subtitle cue with word tokens."""
    def __init__(self, start_frame, end_frame, text):
        self.start_frame = int(start_frame)
        self.end_frame = int(end_frame)
        self.duration_frames = max(1, self.end_frame - self.start_frame)
        self.text = text.strip()
        self.words = self.text.split()
        self.main_word = None

    def __repr__(self):
        return f"<Cue {self.start_frame}-{self.end_frame}: '{self.text}'>"

class SubtitleParser:
    """Handles parsing, chunking, and interactive word re-grouping."""

    @staticmethod
    def clean_punctuation(text, preserve_contractions=True):
        if not text:
            return ""
        if preserve_contractions:
            # Temporarily protect contractions (don't, it's, can't, we're) using unicode private area char
            text = re.sub(r'(?<=[a-zA-Z0-9])[\'’](?=[a-zA-Z0-9])', '\uE000', text)
            # Remove all other punctuation
            text = re.sub(r'[\.,!?;:\"\'\[\]\(\)\{\}\<\>\\\/~`@#\$%\^&\*\-_=+\|]', ' ', text)
            # Restore apostrophes
            text = text.replace('\uE000', "'")
        else:
            text = re.sub(r'[\.,!?;:\"\'\[\]\(\)\{\}\<\>\\\/~`@#\$%\^&\*\-_=+\|]', ' ', text)
        return " ".join(text.split())

    @staticmethod
    def format_case(text, case_mode="as_is"):
        if not text or case_mode == "as_is":
            return text
        if case_mode in ("upper", "all_caps"):
            return text.upper()
        elif case_mode in ("title", "title_case"):
            t = text.title()
            return re.sub(r"([A-Za-z])'([A-Z])", lambda m: m.group(1) + "'" + m.group(2).lower(), t)
        elif case_mode in ("sentence", "sentence_case"):
            s = text.strip()
            return s[:1].upper() + s[1:] if s else s
        return text

    @staticmethod
    def parse_srt_time(time_str):
        time_str = time_str.strip().replace(",", ".")
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600.0 + float(m) * 60.0 + float(s)
        return 0.0

    @classmethod
    def parse_srt_file(cls, filepath, fps=30.0):
        if not os.path.exists(filepath):
            return []

        cues = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if len(lines) < 2:
                continue

            time_line_idx = 1 if lines[0].isdigit() else 0
            if time_line_idx >= len(lines):
                continue

            time_line = lines[time_line_idx]
            match = re.match(r'(\d+:\d+:\d+[\.,]\d+)\s*-->\s*(\d+:\d+:\d+[\.,]\d+)', time_line)
            if not match:
                continue

            t_start = cls.parse_srt_time(match.group(1))
            t_end = cls.parse_srt_time(match.group(2))
            text = " ".join(lines[time_line_idx + 1:])
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = re.sub(r'\{[^\}]+\}', '', clean_text).strip()

            start_frame = int(round(t_start * fps))
            end_frame = int(round(t_end * fps))
            if clean_text:
                cues.append(SubtitleCue(start_frame, end_frame, clean_text))

        return cues

    @classmethod
    def extract_from_timeline(cls, timeline, track_index=1):
        if not timeline:
            return []

        cues = []
        try:
            sub_count = timeline.GetTrackCount("subtitle")
            if sub_count < track_index:
                return []

            items = timeline.GetItemListInTrack("subtitle", track_index)
            if not items:
                return []

            for item in items:
                start = item.GetStart()
                end = item.GetEnd()
                name = item.GetName()
                if name:
                    cues.append(SubtitleCue(start, end, name))
        except Exception as e:
            print(f"[CaptionForge] Error extracting subtitles: {e}")

        return cues

    @classmethod
    def parse_whisper_json(cls, filepath, fps=30.0):
        """
        Parses word-level timestamp JSON (OpenAI Whisper / WhisperX / Descript).
        Extracts individual word tokens with exact start and end frame bounds.
        """
        if not os.path.exists(filepath):
            return []

        import json
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        word_list = []
        if isinstance(data, list):
            word_list = data
        elif isinstance(data, dict):
            if "words" in data and isinstance(data["words"], list):
                word_list = data["words"]
            elif "segments" in data:
                for seg in data["segments"]:
                    if "words" in seg and isinstance(seg["words"], list):
                        word_list.extend(seg["words"])
                    elif "text" in seg and "start" in seg and "end" in seg:
                        word_list.append(seg)

        cues = []
        for w in word_list:
            text = str(w.get("word") or w.get("text") or "").strip()
            if not text:
                continue
            start_sec = float(w.get("start", 0.0))
            end_sec = float(w.get("end", start_sec + 0.35))
            start_f = int(round(start_sec * fps))
            end_f = max(start_f + 4, int(round(end_sec * fps)))
            cues.append(SubtitleCue(start_f, end_f, text))

        return cues

    @classmethod
    def chunk_cues(cls, cues, words_per_slide=2, remove_punctuation=False, case_mode="as_is"):
        if not cues:
            return []

        chunked = []
        for cue in cues:
            raw_text = cue.text
            if remove_punctuation:
                raw_text = cls.clean_punctuation(raw_text, preserve_contractions=True)
            if case_mode != "as_is":
                raw_text = cls.format_case(raw_text, case_mode)

            words = raw_text.split()
            if not words:
                continue

            if words_per_slide <= 0 or len(words) <= words_per_slide:
                chunked.append(SubtitleCue(cue.start_frame, cue.end_frame, " ".join(words)))
                continue

            groups = []
            for i in range(0, len(words), words_per_slide):
                groups.append(" ".join(words[i:i + words_per_slide]))

            cue_start = int(cue.start_frame)
            cue_end = int(cue.end_frame)
            if cue_end <= cue_start:
                cue_end = cue_start + len(groups) * 4
            total_duration = max(len(groups), cue_end - cue_start)
            total_chars = sum(len(g) for g in groups) or len(groups)

            curr_frame = cue_start
            cum_chars = 0
            for idx, grp in enumerate(groups):
                if idx == len(groups) - 1:
                    end_frame = cue_end
                else:
                    cum_chars += len(grp)
                    target = cue_start + int(round(total_duration * (cum_chars / total_chars)))
                    min_end = curr_frame + 1
                    max_end = cue_end - (len(groups) - 1 - idx)
                    end_frame = max(min_end, min(target, max_end))

                chunked.append(SubtitleCue(curr_frame, end_frame, grp))
                curr_frame = end_frame

        return chunked

    @classmethod
    def move_word(cls, plan, from_idx, to_idx, word_idx):
        """Move word between caption groups in the plan preview."""
        if from_idx < 0 or from_idx >= len(plan) or to_idx < 0 or to_idx >= len(plan):
            return
        from_cue = plan[from_idx]
        to_cue = plan[to_idx]
        if word_idx < 0 or word_idx >= len(from_cue.words):
            return

        w = from_cue.words.pop(word_idx)
        to_cue.words.append(w)
        from_cue.text = " ".join(from_cue.words)
        to_cue.text = " ".join(to_cue.words)
