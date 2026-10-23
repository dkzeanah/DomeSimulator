"""Selected production loading; the full registry remains the validation catalogue.

Legacy lessons construct geometry during import. A directed episode should not
wait for every nesting and costing solver before its first frame. Keep these
explicit entry points tied to the same objects registered in lesson_registry.
"""
def get_lesson(key):
    if key == "sketch_gpt_pilot":
        from .lesson_sketch_gpt_episode import SKETCH_GPT_EPISODE
        return SKETCH_GPT_EPISODE
    from .lesson_registry import get_lesson as resolve
    return resolve(key)


def lesson_menu():
    from .lesson_registry import lesson_menu as menu
    return menu()
