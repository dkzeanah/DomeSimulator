"""One ordered stream of prose and illustrations for live, HTML and text readers."""
from .placement import body_segments, figure_groups


def reading_parts(page, assets):
    groups=figure_groups(page,assets)
    for key in groups.get(0,[]):
        yield 'figure',key
    for segment in body_segments(page['body']):
        if segment['markdown']:
            yield 'text',segment['markdown']
        if segment['paragraph'] is not None:
            for key in groups.get(segment['paragraph'],[]):
                yield 'figure',key
    for key in groups.get(None,[]):
        yield 'figure',key
