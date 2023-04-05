from omega_logger.validators import SimpleRange


def test_simple_range():

    class iTHX:

        def log_warning(self, *args, **kwargs):
            pass

    tmin = 15
    tmax = 25
    hmin = 25
    hmax = 60
    dmin = 5
    dmax = 15

    sr = SimpleRange(tmin=tmin, tmax=tmax, hmin=hmin, hmax=hmax, dmin=dmin, dmax=dmax, whatever='silently-ignored')

    ithx = iTHX()

    assert sr.validate(((tmin+tmax)//2, (hmin+hmax)//2, (dmin+dmax)//2), ithx)
    assert sr.validate((tmin, hmin, dmin), ithx)
    assert sr.validate((tmax, hmax, dmax), ithx)
    assert not sr.validate((tmin-1, hmin, dmin), ithx)
    assert not sr.validate((tmin, hmin-1, dmin), ithx)
    assert not sr.validate((tmin, hmin, dmin-1), ithx)
    assert not sr.validate((tmax+1, hmax, dmax), ithx)
    assert not sr.validate((tmax, hmax+1, dmax), ithx)
    assert not sr.validate((tmax, hmax, dmax+1), ithx)

    assert sr.validate(((tmin+tmax)//2, (hmin+hmax)//2, (dmin+dmax)//2,
                        (tmin+tmax)//2, (hmin+hmax)//2, (dmin+dmax)//2), ithx)
    assert sr.validate((tmin, hmin, dmin, tmin, hmin, dmin), ithx)
    assert sr.validate((tmax, hmax, dmax, tmax, hmax, dmax), ithx)

    assert not sr.validate((tmin-1, hmin, dmin, tmin, hmin, dmin), ithx)
    assert not sr.validate((tmin, hmin-1, dmin, tmin, hmin, dmin), ithx)
    assert not sr.validate((tmin, hmin, dmin-1, tmin, hmin, dmin), ithx)
    assert not sr.validate((tmin, hmin, dmin, tmin-1, hmin, dmin), ithx)
    assert not sr.validate((tmin, hmin, dmin, tmin, hmin-1, dmin), ithx)
    assert not sr.validate((tmin, hmin, dmin, tmin, hmin, dmin-1), ithx)

    assert not sr.validate((tmax+1, hmax, dmax, tmax, hmax, dmax), ithx)
    assert not sr.validate((tmax, hmax+1, dmax, tmax, hmax, dmax), ithx)
    assert not sr.validate((tmax, hmax, dmax+1, tmax, hmax, dmax), ithx)
    assert not sr.validate((tmax, hmax, dmax, tmax+1, hmax, dmax), ithx)
    assert not sr.validate((tmax, hmax, dmax, tmax, hmax+1, dmax), ithx)
    assert not sr.validate((tmax, hmax, dmax, tmax, hmax, dmax+1), ithx)
