from app.services.navy_bf import calc_bf


def test_calc_bf_male():
    bf = calc_bf("M", 180, 90, 40, None)
    assert bf > 0


def test_calc_bf_female():
    bf = calc_bf("F", 165, 70, 34, 95)
    assert bf > 0
