# Simple physical example of exponential decay
# with an uncertain piecewise constant coefficient.
# Source: adapted from chaospy.

import numpy as np


# u'(x) = -c(x) u(x) (1)
def eqt(x, c0, c1):
    # Define the piecewise function
    def c(x):
        if x < 0.5:
            return c0
        else:
            return c1

    # Solve the equation (1)
    N = len(x)
    u = np.zeros(N)

    u[0] = 0.3
    for n in range(N-1):
        dx = x[n+1] - x[n]
        K1 = -dx * u[n] * c(x[n])
        K2 = -dx * u[n] + 0.5 * K1 * c(x[n] + 0.5 * dx)
        u[n+1] = u[n] + K1 + K2

    return u
