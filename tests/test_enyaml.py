import os
import sys
import pathlib
import pytest
import enyaml


TESTDIR = pathlib.Path(__file__).parent


@pytest.fixture
def ctx():
    return enyaml.Context()


@pytest.fixture(params=(TESTDIR / 'roundtrips').glob('*.yaml'))
def roundtrip_file(request):
    return request.param


@pytest.fixture
def roundtrip_loader(roundtrip_file):
    with roundtrip_file.open() as f:
        yield enyaml.TemplateLoader(f)


class SENTINEL:
    def __eq__(self, other):
        return other is None or other == 'vvv'
SENTINEL = SENTINEL()


def test_roundtrip(ctx, roundtrip_loader, roundtrip_file):
    while roundtrip_loader.check_data():
        rendered = roundtrip_loader.render_data(ctx)
        assert roundtrip_loader.get_data() == 'vvv'
        expected = roundtrip_loader.get_data()
        assert rendered == expected, str(roundtrip_loader.peek_event().start_mark)
