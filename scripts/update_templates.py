import json, glob, os

SPEC_MAP = {
    'cine_chapter_card': {'pos_y': 0.50, 'bindings': {'chapter_num': 'param:chapter', 'chapter_title': 'param:title'}},
    'cine_intertitle_card': {'pos_y': 0.50, 'bindings': {'card': 'param:card_text'}},
    'cine_main_title': {'pos_y': 0.50, 'bindings': {'title': 'param:title', 'credit': 'param:director'}},
    'doc_archive_caption': {'pos_y': 0.20, 'bindings': {'src': 'param:source', 'sub': 'param:subject'}},
    'doc_interviewee_rule': {'pos_y': 0.22, 'bindings': {'name_text': 'param:name', 'role_text': 'param:role'}},
    'doc_timestamp_hud': {'pos_y': 0.22, 'bindings': {'loc': 'param:location', 'tc': 'param:timecode'}},
    'edit_drop_cap': {'pos_y': 0.50, 'bindings': {'heading': 'param:heading', 'body': 'param:body'}},
    'edit_issue_tag': {'pos_y': 0.26, 'bindings': {'issue': 'param:issue', 'topic': 'param:topic'}},
    'edit_pull_quote': {'pos_y': 0.50, 'bindings': {'quote': 'param:quote', 'author': 'param:author'}},
    'edit_section_opener': {'pos_y': 0.50, 'bindings': {'num': 'param:section_num', 'name': 'param:section_name'}},
    'edit_serif_headline': {'pos_y': 0.50, 'bindings': {'category_tag': 'param:tag', 'headline_1': 'param:line1', 'headline_2': 'param:line2'}},
    'edit_split_weight': {'pos_y': 0.50, 'bindings': {'l1': 'param:line1', 'l2': 'param:line2'}},
    'kin_dynamic_stack': {'pos_y': 0.50, 'bindings': {'top': 'param:top_word', 'bottom': 'param:bottom_word'}},
    'kin_masked_line': {'pos_y': 0.50, 'bindings': {'line_1': 'param:line1', 'line_2': 'param:line2'}},
    'kin_word_pop': {'pos_y': 0.50, 'bindings': {'word': 'param:word'}},
    'min_centered_statement': {'pos_y': 0.50, 'bindings': {'stmt': 'param:statement'}},
    'min_corner_tag': {'pos_y': 0.84, 'bindings': {'tag': 'param:tag_text'}},
    'min_outro_title': {'pos_y': 0.50, 'bindings': {'title': 'param:title', 'sub': 'param:sub'}},
    'min_single_line': {'pos_y': 0.50, 'bindings': {'text': 'param:text'}},
    'min_subtitle_hairline': {'pos_y': 0.50, 'bindings': {'main_title': 'param:title', 'sub_title': 'param:subtitle'}},
    'min_underline_reveal': {'pos_y': 0.50, 'bindings': {'headline': 'param:headline'}},
    'pod_captions_highlight': {'pos_y': 0.24, 'bindings': {'caption': 'param:caption_text'}},
    'pod_chapter_marker': {'pos_y': 0.24, 'bindings': {'chap_num': 'param:chap_num', 'chap_title': 'param:chap_title'}},
    'pod_episode_card': {'pos_y': 0.50, 'bindings': {'ep_num': 'param:ep_num', 'title': 'param:title'}},
    'pod_lower_third_slate': {'pos_y': 0.22, 'bindings': {'guest_name': 'param:name', 'guest_role': 'param:role'}},
    'pod_outro_card': {'pos_y': 0.50, 'bindings': {'headline': 'param:headline', 'channel': 'param:channel'}},
    'pod_quote_card': {'pos_y': 0.50, 'bindings': {'quote': 'param:quote_text', 'author': 'param:author'}},
    'pod_speaker_switch': {'pos_y': 0.22, 'bindings': {'speaker_name': 'param:speaker_name', 'topic_label': 'param:topic_label'}},
    'pod_talking_about': {'pos_y': 0.22, 'bindings': {'topic': 'param:topic', 'badge': 'param:badge_label'}},
    'saas_bento_grid': {'pos_y': 0.50, 'bindings': {'title': 'param:bento_title', 'cat': 'param:bento_cat'}},
    'saas_changelog_title': {'pos_y': 0.28, 'bindings': {'ver': 'param:version', 'feat': 'param:feature'}},
    'saas_cta_card': {'pos_y': 0.50, 'bindings': {'cta': 'param:cta_text', 'url': 'param:url'}},
    'saas_feature_callout': {'pos_y': 0.28, 'bindings': {'card_title': 'param:title', 'card_desc': 'param:desc'}},
    'saas_glass_card': {'pos_y': 0.50, 'bindings': {'title': 'param:card_title', 'desc': 'param:card_desc'}},
    'saas_gradient_headline': {'pos_y': 0.50, 'bindings': {'headline': 'param:headline'}},
    'saas_pill_badge': {'pos_y': 0.24, 'bindings': {'tag': 'param:badge_tag', 'desc': 'param:badge_desc'}},
    'saas_shortcut_chips': {'pos_y': 0.25, 'bindings': {'keys': 'param:shortcut', 'action': 'param:action'}},
    'saas_stat_counter': {'pos_y': 0.50, 'bindings': {'stat': 'param:stat_number', 'label': 'param:stat_label'}},
    'saas_step_titles': {'pos_y': 0.50, 'bindings': {'num': 'param:step_num', 'step': 'param:step_title'}},
    'soc_3line_stack': {'pos_y': 0.50, 'bindings': {'l1': 'param:l1', 'l2': 'param:l2'}},
    'soc_hook_pop': {'pos_y': 0.35, 'bindings': {'hook_text': 'param:hook', 'sub_text': 'param:sub'}},
    'soc_keyword_box': {'pos_y': 0.28, 'bindings': {'text': 'param:text'}},
    'soc_link_bio': {'pos_y': 0.24, 'bindings': {'cta': 'param:cta', 'sub': 'param:sub'}},
    'soc_progress_marker': {'pos_y': 0.26, 'bindings': {'step': 'param:step_text', 'desc': 'param:desc'}},
    'soc_reaction_tag': {'pos_y': 0.28, 'bindings': {'rx': 'param:reaction'}},
    'soc_split_twotone': {'pos_y': 0.50, 'bindings': {'lead': 'param:hook_lead', 'core': 'param:hook_core'}}
}

updated = 0
for path in sorted(glob.glob('data/templates/*/*.json')):
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    tid = d.get('id')
    spec = SPEC_MAP.get(tid)
    if not spec:
        continue
    
    # 1. Ensure pos_y parameter exists and is updated
    pos_y_found = False
    for p in d.get('parameters', []):
        if p.get('id') == 'pos_y':
            p['default'] = spec['pos_y']
            pos_y_found = True
            break
            
    if not pos_y_found:
        d.setdefault('parameters', []).append({
            "id": "pos_y",
            "name": "Vertical Position",
            "type": "number",
            "default": spec['pos_y'],
            "min_val": 0.1,
            "max_val": 0.85,
            "step": 0.01,
            "category": "Layout"
        })
            
    # 2. Update layer text bindings
    bindings = spec.get('bindings', {})
    for l in d.get('layers', []):
        lid = l.get('id')
        if lid in bindings:
            if 'props' not in l:
                l['props'] = {}
            l['props']['text'] = bindings[lid]
            
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    updated += 1

print(f"Updated {updated} template JSON specs successfully!")
