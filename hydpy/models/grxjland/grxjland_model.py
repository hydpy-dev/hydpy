# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
import numpy
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
# ...from grxjland
from hydpy.models.grxjland import grxjland_inputs
from hydpy.models.grxjland import grxjland_fluxes
from hydpy.models.grxjland import grxjland_control
from hydpy.models.grxjland import grxjland_states
from hydpy.models.grxjland import grxjland_outlets
from hydpy.models.grxjland import grxjland_derived
from hydpy.models.grxjland import grxjland_logs


class Calc_PSnowLayer_V1(modeltools.Method):
    """ Calculate precipitation for each snow layer.
        Basic equations:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> pub.options.reprdigits = 6
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1636)
        >>> derived.zlayers(1052., 1389., 1626., 1822., 2013.)
        >>> inputs.p = 7.09
        >>> model.calc_psnowlayer_v1()
        >>> fluxes.player
        player(5.656033, 6.494091, 7.156799, 7.755659, 8.387418)

        Elevation of ZLayers > 4000, precipitation doesn't changes with elevation any more

        >>> derived.zlayers(1052., 1389., 1626., 4500., 6300.)
        >>> model.calc_psnowlayer_v1()
        >>> fluxes.player
        player(3.505863, 4.02533, 4.436105, 11.741351, 11.741351)

    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.Z,
    )

    DERIVEDPARAMETERS = (
        grxjland_derived.ZLayers,
    )

    REQUIREDSEQUENCES = (
        grxjland_inputs.P,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.PLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_gradp = 0.00041
        d_zthreshold = 4000.
        # calculate mean precipitation to scale
        d_meanplayer = 0.
        for k in range(con.nsnowlayers):
            if der.zlayers[k] < d_zthreshold:
                flu.player[k] = inp.p * modelutils.exp(d_gradp * (der.zlayers[k] - con.z))
            elif der.zlayers[k] > d_zthreshold:
                flu.player[k] = inp.p * modelutils.exp(d_gradp * (d_zthreshold - con.z))
            else:
                flu.player[k] = inp.p
            d_meanplayer = d_meanplayer + flu.player[k] / con.nsnowlayers
        # scale precipitation, that the mean of yone precipitation is equal to the subbasin precipitation
        if d_meanplayer > 0.:
            for k in range(con.nsnowlayers):
                flu.player[k] = flu.player[k] / d_meanplayer * inp.p

class Calc_TSnowLayer_V1(modeltools.Method):
    """ Calculate daily mean temperature for each snow layer in dependence of elevation.

        Basic equation:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1636)
        >>> derived.zlayers(1052., 1389., 1626., 1822., 2013.)

        Define temperature gradient for each day in year

        >>> gradtmean(0.434, 0.434, 0.435, 0.436, 0.437, 0.439, 0.44, 0.441, 0.442, 0.444, 0.445, 0.446, 0.448,
        ...     0.45, 0.451, 0.453, 0.455, 0.456, 0.458, 0.46, 0.462, 0.464, 0.466, 0.468, 0.47, 0.472,
        ...     0.474, 0.476, 0.478, 0.48, 0.483, 0.485, 0.487, 0.489, 0.492, 0.494, 0.496, 0.498, 0.501,
        ...     0.503, 0.505, 0.508, 0.51, 0.512, 0.515, 0.517, 0.519, 0.522, 0.524, 0.526, 0.528, 0.53, 0.533,
        ...     0.535, 0.537, 0.539, 0.541, 0.543, 0.545, 0.546, 0.547, 0.549, 0.551, 0.553, 0.555, 0.557, 0.559,
        ...     0.56, 0.562, 0.564, 0.566, 0.567, 0.569, 0.57, 0.572, 0.573, 0.575, 0.576, 0.577, 0.579, 0.58, 0.581,
        ...     0.582, 0.583, 0.584, 0.585, 0.586, 0.587, 0.588, 0.589, 0.59, 0.591, 0.591, 0.592, 0.593, 0.593,
        ...     0.594, 0.595, 0.595, 0.596, 0.596, 0.597, 0.597, 0.597, 0.598, 0.598, 0.598, 0.599, 0.599, 0.599,
        ...     0.599, 0.6, 0.6, 0.6, 0.6, 0.6, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.601, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.6, 0.6, 0.6, 0.6,
        ...     0.599, 0.599, 0.599, 0.598, 0.598, 0.598, 0.597, 0.597, 0.597, 0.596, 0.596, 0.595, 0.595, 0.594, 0.594,
        ...     0.593, 0.593, 0.592, 0.592, 0.591, 0.59, 0.59, 0.589, 0.588, 0.588, 0.587, 0.586, 0.586, 0.585, 0.584,
        ...     0.583, 0.583, 0.582, 0.581, 0.58, 0.579, 0.578, 0.578, 0.577, 0.576, 0.575, 0.574, 0.573, 0.572, 0.571,
        ...     0.57, 0.569, 0.569, 0.568, 0.567, 0.566, 0.565, 0.564, 0.563, 0.562, 0.561, 0.56, 0.558, 0.557, 0.556,
        ...     0.555, 0.554, 0.553, 0.552, 0.551, 0.55, 0.549, 0.548, 0.546, 0.545, 0.544, 0.543, 0.542, 0.541, 0.54,
        ...     0.538, 0.537, 0.536, 0.535, 0.533, 0.532, 0.531, 0.53, 0.528, 0.527, 0.526, 0.525, 0.523, 0.522, 0.521,
        ...     0.519, 0.518, 0.517, 0.515, 0.514, 0.512, 0.511, 0.51, 0.508, 0.507, 0.505, 0.504, 0.502, 0.501, 0.499,
        ...     0.498, 0.496, 0.495, 0.493, 0.492, 0.49, 0.489, 0.487, 0.485, 0.484, 0.482, 0.481, 0.479, 0.478, 0.476,
        ...     0.475, 0.473, 0.471, 0.47, 0.468, 0.467, 0.465, 0.464, 0.462, 0.461, 0.459, 0.458, 0.456, 0.455, 0.454,
        ...     0.452, 0.451, 0.45, 0.448, 0.447, 0.446, 0.445, 0.443, 0.442, 0.441, 0.44, 0.439, 0.438, 0.437, 0.436,
        ...     0.435, 0.434, 0.434, 0.433, 0.432, 0.431, 0.431, 0.43, 0.43, 0.429, 0.429, 0.429, 0.428, 0.428, 0.428,
        ...     0.428, 0.428, 0.428, 0.428, 0.428, 0.429, 0.429, 0.429, 0.43, 0.43, 0.431, 0.431, 0.432, 0.433)
        >>> inputs.t = -1.60835

        Now we prepare a |DOY| object, that assumes that the first, second,
        and third simulation time steps are first, second and third day of year, respectively :

        >>> derived.doy.shape = 3
        >>> derived.doy = 0, 1, 2
        >>> model.idx_sim = 1

        >>> model.calc_tsnowlayer_v1()
        >>> fluxes.tlayer
        tlayer(0.92621, -0.53637, -1.56495, -2.41559, -3.24453)

        Second simulation step

        >>> inputs.t = -2.44165
        >>> model.calc_tsnowlayer_v1()
        >>> fluxes.tlayer
        tlayer(0.09291, -1.36967, -2.39825, -3.24889, -4.07783)

        Third simulation step

        >>> inputs.t = -10.41945
        >>> model.calc_tsnowlayer_v1()
        >>> fluxes.tlayer
        tlayer(-7.88489, -9.34747, -10.37605, -11.22669, -12.05563)

    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.Z,
        grxjland_control.GradTMean,
    )

    DERIVEDPARAMETERS = (
        grxjland_derived.ZLayers,
        grxjland_derived.DOY,
    )

    REQUIREDSEQUENCES = (
        grxjland_inputs.T,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.TLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            flu.tlayer[k] = inp.t + (con.z - der.zlayers[k]) * modelutils.fabs(con.gradtmean[der.doy[model.idx_sim]]) / 100.


class Calc_TSnowLayer_V2(modeltools.Method):
    """ Calculate daily mean, minimum, maximum air temperature for each snow layer in dependence of elevation.

        Basic equation:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1636)
        >>> derived.zlayers(1052., 1389., 1626., 1822., 2013.)

        Define temperature gradients for each day in year

        >>> gradtmean(0.434, 0.434, 0.435, 0.436, 0.437, 0.439, 0.44, 0.441, 0.442, 0.444, 0.445, 0.446, 0.448,
        ...     0.45, 0.451, 0.453, 0.455, 0.456, 0.458, 0.46, 0.462, 0.464, 0.466, 0.468, 0.47, 0.472,
        ...     0.474, 0.476, 0.478, 0.48, 0.483, 0.485, 0.487, 0.489, 0.492, 0.494, 0.496, 0.498, 0.501,
        ...     0.503, 0.505, 0.508, 0.51, 0.512, 0.515, 0.517, 0.519, 0.522, 0.524, 0.526, 0.528, 0.53, 0.533,
        ...     0.535, 0.537, 0.539, 0.541, 0.543, 0.545, 0.546, 0.547, 0.549, 0.551, 0.553, 0.555, 0.557, 0.559,
        ...     0.56, 0.562, 0.564, 0.566, 0.567, 0.569, 0.57, 0.572, 0.573, 0.575, 0.576, 0.577, 0.579, 0.58, 0.581,
        ...     0.582, 0.583, 0.584, 0.585, 0.586, 0.587, 0.588, 0.589, 0.59, 0.591, 0.591, 0.592, 0.593, 0.593,
        ...     0.594, 0.595, 0.595, 0.596, 0.596, 0.597, 0.597, 0.597, 0.598, 0.598, 0.598, 0.599, 0.599, 0.599,
        ...     0.599, 0.6, 0.6, 0.6, 0.6, 0.6, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.601, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.6, 0.6, 0.6, 0.6,
        ...     0.599, 0.599, 0.599, 0.598, 0.598, 0.598, 0.597, 0.597, 0.597, 0.596, 0.596, 0.595, 0.595, 0.594, 0.594,
        ...     0.593, 0.593, 0.592, 0.592, 0.591, 0.59, 0.59, 0.589, 0.588, 0.588, 0.587, 0.586, 0.586, 0.585, 0.584,
        ...     0.583, 0.583, 0.582, 0.581, 0.58, 0.579, 0.578, 0.578, 0.577, 0.576, 0.575, 0.574, 0.573, 0.572, 0.571,
        ...     0.57, 0.569, 0.569, 0.568, 0.567, 0.566, 0.565, 0.564, 0.563, 0.562, 0.561, 0.56, 0.558, 0.557, 0.556,
        ...     0.555, 0.554, 0.553, 0.552, 0.551, 0.55, 0.549, 0.548, 0.546, 0.545, 0.544, 0.543, 0.542, 0.541, 0.54,
        ...     0.538, 0.537, 0.536, 0.535, 0.533, 0.532, 0.531, 0.53, 0.528, 0.527, 0.526, 0.525, 0.523, 0.522, 0.521,
        ...     0.519, 0.518, 0.517, 0.515, 0.514, 0.512, 0.511, 0.51, 0.508, 0.507, 0.505, 0.504, 0.502, 0.501, 0.499,
        ...     0.498, 0.496, 0.495, 0.493, 0.492, 0.49, 0.489, 0.487, 0.485, 0.484, 0.482, 0.481, 0.479, 0.478, 0.476,
        ...     0.475, 0.473, 0.471, 0.47, 0.468, 0.467, 0.465, 0.464, 0.462, 0.461, 0.459, 0.458, 0.456, 0.455, 0.454,
        ...     0.452, 0.451, 0.45, 0.448, 0.447, 0.446, 0.445, 0.443, 0.442, 0.441, 0.44, 0.439, 0.438, 0.437, 0.436,
        ...     0.435, 0.434, 0.434, 0.433, 0.432, 0.431, 0.431, 0.43, 0.43, 0.429, 0.429, 0.429, 0.428, 0.428, 0.428,
        ...     0.428, 0.428, 0.428, 0.428, 0.428, 0.429, 0.429, 0.429, 0.43, 0.43, 0.431, 0.431, 0.432, 0.433)
        >>> gradtmin(0.366, 0.366, 0.367, 0.367, 0.367, 0.367, 0.367, 0.368, 0.368, 0.368, 0.368, 0.368, 0.369, 0.369,
        ...    0.369, 0.37, 0.37, 0.37, 0.371, 0.371, 0.371, 0.372, 0.372, 0.373, 0.373, 0.374, 0.374, 0.375, 0.375, 0.376,
        ...    0.376, 0.377, 0.377, 0.378, 0.379, 0.379, 0.38, 0.381, 0.381, 0.382, 0.383, 0.384, 0.384, 0.385, 0.386,
        ...    0.387, 0.387, 0.388, 0.389, 0.39, 0.391, 0.392, 0.393, 0.393, 0.394, 0.395, 0.396, 0.397, 0.398, 0.399,
        ...    0.399, 0.4, 0.401, 0.402, 0.403, 0.404, 0.405, 0.406, 0.406, 0.407, 0.408, 0.409, 0.41, 0.411, 0.412,
        ...    0.413, 0.414, 0.415, 0.416, 0.417, 0.417, 0.418, 0.419, 0.42, 0.421, 0.422, 0.422, 0.423, 0.424, 0.425,
        ...    0.425, 0.426, 0.427, 0.427, 0.428, 0.429, 0.429, 0.43, 0.431, 0.431, 0.432, 0.432, 0.433, 0.433, 0.434,
        ...    0.434, 0.435, 0.435, 0.436, 0.436, 0.436, 0.437, 0.437, 0.437, 0.438, 0.438, 0.438, 0.438, 0.439,
        ...    0.439, 0.439, 0.439, 0.439, 0.439, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44,
        ...    0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.439, 0.439, 0.439, 0.439,
        ...    0.439, 0.439, 0.439, 0.439, 0.439, 0.439, 0.438, 0.438, 0.438, 0.438, 0.438, 0.438, 0.438, 0.438, 0.438,
        ...    0.437, 0.437, 0.437, 0.437, 0.437, 0.437, 0.437, 0.436, 0.436, 0.436, 0.436, 0.436, 0.436, 0.436, 0.435,
        ...    0.435, 0.435, 0.435, 0.435, 0.434, 0.434, 0.434, 0.434, 0.434, 0.433, 0.433, 0.433, 0.433, 0.432, 0.432,
        ...    0.432, 0.432, 0.431, 0.431, 0.431, 0.43, 0.43, 0.43, 0.429, 0.429, 0.428, 0.428, 0.428, 0.427, 0.427,
        ...    0.426, 0.426, 0.425, 0.425, 0.424, 0.424, 0.423, 0.423, 0.422, 0.421, 0.421, 0.42, 0.42, 0.419, 0.418,
        ...    0.418, 0.417, 0.416, 0.415, 0.415, 0.414, 0.413, 0.413, 0.412, 0.411, 0.41, 0.409, 0.409, 0.408, 0.407,
        ...    0.406, 0.405, 0.405, 0.404, 0.403, 0.402, 0.401, 0.401, 0.4, 0.399, 0.398, 0.397, 0.396, 0.396, 0.395,
        ...    0.394, 0.393, 0.392, 0.391, 0.391, 0.39, 0.389, 0.388, 0.388, 0.387, 0.386, 0.385, 0.385, 0.384, 0.383,
        ...    0.383, 0.382, 0.381, 0.381, 0.38, 0.379, 0.379, 0.378, 0.377, 0.377, 0.376, 0.376, 0.375, 0.375, 0.374,
        ...    0.374, 0.373, 0.373, 0.372, 0.372, 0.372, 0.371, 0.371, 0.371, 0.37, 0.37, 0.37, 0.369, 0.369, 0.369,
        ...    0.368, 0.368, 0.368, 0.368, 0.368, 0.367, 0.367, 0.367, 0.367, 0.367, 0.367, 0.366, 0.366, 0.366, 0.366,
        ...    0.366, 0.366, 0.366, 0.366, 0.366, 0.366, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365,
        ...    0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365,
        ...    0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.366, 0.366, 0.366,
        ...    0.366, 0.366, 0.366, 0.366, 0.366)
        >>> gradtmax(0.498, 0.5, 0.501, 0.503, 0.504, 0.506, 0.508, 0.51, 0.512, 0.514, 0.517, 0.519, 0.522, 0.525, 0.527,
        ...    0.53, 0.533, 0.537, 0.54, 0.543, 0.547, 0.55, 0.554, 0.558, 0.561, 0.565, 0.569, 0.573, 0.577, 0.582,
        ...    0.586, 0.59, 0.594, 0.599, 0.603, 0.607, 0.612, 0.616, 0.621, 0.625, 0.63, 0.634, 0.639, 0.643, 0.648,
        ...    0.652, 0.657, 0.661, 0.666, 0.67, 0.674, 0.679, 0.683, 0.687, 0.691, 0.695, 0.699, 0.703, 0.707, 0.709,
        ...    0.711, 0.715, 0.718, 0.722, 0.726, 0.729, 0.732, 0.736, 0.739, 0.742, 0.745, 0.748, 0.75, 0.753, 0.756,
        ...    0.758, 0.761, 0.763, 0.765, 0.767, 0.769, 0.771, 0.773, 0.774, 0.776, 0.777, 0.779, 0.78, 0.781, 0.782,
        ...    0.783, 0.784, 0.785, 0.785, 0.786, 0.787, 0.787, 0.787, 0.788, 0.788, 0.788, 0.788, 0.788, 0.788, 0.788,
        ...    0.788, 0.787, 0.787, 0.787, 0.786, 0.786, 0.785, 0.785, 0.784, 0.784, 0.783, 0.783, 0.782, 0.781, 0.781,
        ...    0.78, 0.779, 0.778, 0.778, 0.777, 0.776, 0.775, 0.775, 0.774, 0.773, 0.772, 0.772, 0.771, 0.77, 0.77,
        ...    0.769, 0.768, 0.768, 0.767, 0.767, 0.766, 0.766, 0.765, 0.765, 0.764, 0.764, 0.764, 0.763, 0.763, 0.763,
        ...    0.762, 0.762, 0.762, 0.762, 0.762, 0.762, 0.762, 0.761, 0.761, 0.761, 0.761, 0.761, 0.762, 0.762, 0.762,
        ...    0.762, 0.762, 0.762, 0.762, 0.762, 0.763, 0.763, 0.763, 0.763, 0.763, 0.764, 0.764, 0.764, 0.764, 0.764,
        ...    0.765, 0.765, 0.765, 0.765, 0.765, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.767,
        ...    0.767, 0.767, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.766, 0.765, 0.765, 0.765, 0.765, 0.764, 0.764,
        ...    0.764, 0.763, 0.763, 0.762, 0.762, 0.761, 0.761, 0.76, 0.76, 0.759, 0.758, 0.758, 0.757, 0.756, 0.755,
        ...    0.754, 0.754, 0.753, 0.752, 0.751, 0.75, 0.749, 0.748, 0.747, 0.746, 0.745, 0.744, 0.743, 0.742, 0.741,
        ...    0.74, 0.738, 0.737, 0.736, 0.735, 0.734, 0.732, 0.731, 0.73, 0.728, 0.727, 0.725, 0.724, 0.723, 0.721,
        ...    0.72, 0.718, 0.717, 0.715, 0.713, 0.712, 0.71, 0.709, 0.707, 0.705, 0.703, 0.702, 0.7, 0.698, 0.696,
        ...    0.694, 0.692, 0.69, 0.688, 0.686, 0.684, 0.682, 0.68, 0.678, 0.676, 0.674, 0.671, 0.669, 0.667, 0.664,
        ...    0.662, 0.659, 0.657, 0.654, 0.652, 0.649, 0.647, 0.644, 0.641, 0.639, 0.636, 0.633, 0.63, 0.628, 0.625,
        ...    0.622, 0.619, 0.616, 0.613, 0.61, 0.607, 0.604, 0.601, 0.598, 0.595, 0.592, 0.589, 0.586, 0.583, 0.58,
        ...    0.577, 0.574, 0.571, 0.568, 0.565, 0.562, 0.559, 0.556, 0.553, 0.55, 0.547, 0.544, 0.542, 0.539, 0.536,
        ...    0.533, 0.531, 0.528, 0.526, 0.523, 0.521, 0.519, 0.517, 0.515, 0.513, 0.511, 0.509, 0.507, 0.505, 0.504,
        ...    0.502, 0.501, 0.5, 0.498, 0.497, 0.496, 0.496, 0.495, 0.494, 0.494, 0.494, 0.493, 0.493, 0.493, 0.493,
        ...    0.494, 0.494, 0.495, 0.495, 0.496, 0.497)
        >>> inputs.t = -1.60835
        >>> inputs.tmin = -3.2
        >>> inputs.tmax = 2.2

        Now we prepare a |DOY| object, that assumes that the first, second,
        and third simulation time steps are first, second and third day of year, respectively :

        >>> derived.doy.shape = 3
        >>> derived.doy = 0, 1, 2
        >>> model.idx_sim = 1

        >>> model.calc_tsnowlayer_v2()
        >>> fluxes.tlayer
        tlayer(0.92621, -0.53637, -1.56495, -2.41559, -3.24453)
        >>> fluxes.tminlayer
        tminlayer(-1.06256, -2.29598, -3.1634, -3.88076, -4.57982)
        >>> fluxes.tmaxlayer
        tmaxlayer(5.12, 3.435, 2.25, 1.27, 0.315)

        Second simulation step

        >>> inputs.t = -2.44165
        >>> inputs.tmin = -5.1
        >>> inputs.tmax = 0.3
        >>> model.calc_tsnowlayer_v2()
        >>> fluxes.tlayer
        tlayer(0.09291, -1.36967, -2.39825, -3.24889, -4.07783)
        >>> fluxes.tminlayer
        tminlayer(-2.96256, -4.19598, -5.0634, -5.78076, -6.47982)
        >>> fluxes.tmaxlayer
        tmaxlayer(3.22, 1.535, 0.35, -0.63, -1.585)

        Third simulation step

        >>> inputs.t = -10.41945
        >>> inputs.tmin = -16.3
        >>> inputs.tmax = -5.3
        >>> model.calc_tsnowlayer_v2()
        >>> fluxes.tlayer
        tlayer(-7.88489, -9.34747, -10.37605, -11.22669, -12.05563)
        >>> fluxes.tminlayer
        tminlayer(-14.16256, -15.39598, -16.2634, -16.98076, -17.67982)
        >>> fluxes.tmaxlayer
        tmaxlayer(-2.38, -4.065, -5.25, -6.23, -7.185)

    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.Z,
        grxjland_control.GradTMean,
        grxjland_control.GradTMax,
        grxjland_control.GradTMin,

    )

    DERIVEDPARAMETERS = (
        grxjland_derived.ZLayers,
        grxjland_derived.DOY,
    )

    REQUIREDSEQUENCES = (
        grxjland_inputs.T,
        grxjland_inputs.TMin,
        grxjland_inputs.TMax,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.TLayer,
        grxjland_fluxes.TMinLayer,
        grxjland_fluxes.TMaxLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            flu.tlayer[k] = inp.t + (con.z - der.zlayers[k]) * modelutils.fabs(con.gradtmean[der.doy[model.idx_sim]]) / 100.
            flu.tminlayer[k] = inp.tmin + (con.z - der.zlayers[k]) * modelutils.fabs(con.gradtmin[der.doy[model.idx_sim]]) / 100.
            flu.tmaxlayer[k] = inp.tmax + (con.z - der.zlayers[k]) * modelutils.fabs(con.gradtmax[der.doy[model.idx_sim]]) / 100.


class Calc_FracSolidPrec_V1(modeltools.Method):
    """ Calculate solid precipitation fraction [/] for each snow layer.

        Basic equation:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> fluxes.tlayer = 0.92621, -0.53637, -1.56495, -2.41559, -3.24453
        >>> fluxes.player = 5.656033, 6.494091, 7.156799, 7.755659, 8.387418

        >>> model.calc_fracsolidprec_v1()
        >>> fluxes.solidfraction
        solidfraction(0.518447, 0.884092, 1.0, 1.0, 1.0)
        >>> fluxes.psnowlayer
        psnowlayer(2.932356, 5.741377, 7.156799, 7.755659, 8.387418)
        >>> fluxes.prainlayer
        prainlayer(2.723677, 0.752714, 0.0, 0.0, 0.0)

    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
    )

    REQUIREDSEQUENCES = (
        grxjland_fluxes.TLayer,
        grxjland_fluxes.PLayer,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.SolidFraction,
        grxjland_fluxes.PSnowLayer,
        grxjland_fluxes.PRainLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            flu.solidfraction[k] = min(1, max(0, 1. - (flu.tlayer[k] + 1.) / (3.0 + 1.0)))
            flu.psnowlayer[k] = flu.solidfraction[k] *  flu.player[k]
            flu.prainlayer[k] = (1. - flu.solidfraction[k] ) * flu.player[k]

class Calc_FracSolidPrec_V2(modeltools.Method):
    """ Calculate solid precipitation fraction [/] for each snow layer.

        Basic equation:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1000)
        >>> fluxes.tlayer = 0.92621, -0.53637, -1.56495, -2.41559, -3.24453
        >>> fluxes.tminlayer = -1.06256, -2.29598, -3.1634, -3.88076, -4.57982
        >>> fluxes.tmaxlayer =  5.12, 3.435, 2.25, 1.27, 0.315
        >>> fluxes.player = 5.656033, 6.494091, 7.156799, 7.755659, 8.387418
        >>> model.calc_fracsolidprec_v2()
        >>> fluxes.solidfraction
        solidfraction(0.171864, 0.400626, 0.584365, 0.753434, 0.935646)
        >>> fluxes.psnowlayer
        psnowlayer(0.972069, 2.601702, 4.182181, 5.843381, 7.847656)
        >>> fluxes.prainlayer
        prainlayer(4.683964, 3.892389, 2.974618, 1.912278, 0.539762)

    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.Z,
    )

    REQUIREDSEQUENCES = (
        grxjland_fluxes.TLayer,
        grxjland_fluxes.PLayer,
        grxjland_fluxes.TMinLayer,
        grxjland_fluxes.TMaxLayer,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.SolidFraction,
        grxjland_fluxes.PSnowLayer,
        grxjland_fluxes.PRainLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            if con.z < 1500.:
                flu.solidfraction[k] = min(1, max(0, 1. - flu.tmaxlayer[k] / (flu.tmaxlayer[k] - flu.tminlayer[k])))
            else:
                flu.solidfraction[k] = min(1, max(0, 1. - (flu.tlayer[k] + 1.) / (3.0 + 1.0)))
            flu.psnowlayer[k] = flu.solidfraction[k] * flu.player[k]
            flu.prainlayer[k] = (1. - flu.solidfraction[k]) * flu.player[k]

class Calc_SnowPack_V1(modeltools.Method):
    """ Calculate snow accumulation for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip(83., 83., 83., 83., 83.)
        >>> cn1(0.962)
        >>> cn2(2.249)
        >>> fluxes.tlayer =  -0.22318, -0.67402, -1.17348, -1.77018, -2.63208
        >>> fluxes.psnowlayer =  0.07273111, 0.086444894,  0.09857770,  0.10418780,  0.11285966
        >>> states.g = 0., 0., 0., 0., 0.
        >>> states.etg = 0., 0., 0., 0., 0.
        >>> states.gratio = 0., 0., 0., 0., 0.
        >>> model.calc_snowpack_v1()
        >>> states.g
        g(0.072731, 0.086445, 0.098578, 0.104188, 0.11286)
        >>> states.etg
        etg(-0.008481, -0.025613, -0.044592, -0.067267, -0.100019)
        >>> states.gratio
        gratio(0.000974, 0.001157, 0.00132, 0.001395, 0.001511)
        >>> fluxes.potmelt
        potmelt(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0)

        New Input data

        >>> fluxes.tlayer = 2.18124, 1.72836, 1.22664, 0.62724, -0.23856
        >>> fluxes.psnowlayer = 0.03695066, 0.059840058, 0.08740688, 0.12360633, 0.18275139
        >>> model.calc_snowpack_v1()
        >>> states.g
        g(0.098569, 0.131399, 0.166969, 0.227794, 0.295611)
        >>> states.etg
        etg(0.0, 0.0, 0.0, -0.040876, -0.105284)
        >>> states.gratio
        gratio(0.00132, 0.001759, 0.002235, 0.003049, 0.003957)
        >>> fluxes.potmelt
        potmelt(0.109682, 0.146285, 0.185985, 0.0, 0.0)
        >>> fluxes.melt
        melt(0.011113, 0.014886, 0.019015, 0.0, 0.0)

        New Input data

        >>> fluxes.tlayer = 3.58345, 3.12955, 2.62670, 2.02595, 1.15820
        >>> fluxes.psnowlayer = 0., 0., 0.26679315, 0.73575994, 1.50702064

        >>> model.calc_snowpack_v1()
        >>> states.g
        g(0.088595, 0.118051, 0.388119, 0.856013, 1.802632)
        >>> states.etg
        etg(0.0, 0.0, 0.0, 0.0, -0.057271)
        >>> states.gratio
        gratio(0.001186, 0.00158, 0.005196, 0.011459, 0.024132)
        >>> fluxes.potmelt
        potmelt(0.098569, 0.131399, 0.433763, 0.963554, 0.0)
        >>> fluxes.melt
        melt(0.009974, 0.013348, 0.045643, 0.107541, 0.0)
    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.MeanAnSolidPrecip,
        grxjland_control.CN1,
        grxjland_control.CN2,
    )

    REQUIREDSEQUENCES = (
        grxjland_fluxes.TLayer,
        grxjland_fluxes.PSnowLayer,
    )
    UPDATEDSEQUENCES = (
        grxjland_states.G,
        grxjland_states.ETG,
        grxjland_states.GRatio,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.PotMelt,
        grxjland_fluxes.Melt,

    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        d_tmelt = 0.
        d_minspeed = 0.1

        for k in range(con.nsnowlayers):
            d_gthreshold = 0.9 * con.meanansolidprecip[k]
            # update snow pack
            sta.g[k] = sta.g[k] + flu.psnowlayer[k]
            # thermal state before melt
            sta.etg[k] = min(0, con.cn1 * sta.etg[k] + (1. - con.cn1) * flu.tlayer[k])
            #potential melt
            if sta.etg[k] == 0 and flu.tlayer[k] > 0:
                flu.potmelt[k] = min(sta.g[k], con.cn2 * (flu.tlayer[k] - d_tmelt))
            else:
                flu.potmelt[k] = 0
            # snow covered area computation
            if sta.g[k] < d_gthreshold:
                sta.gratio[k] = sta.g[k] / d_gthreshold
            else:
                sta.gratio[k] = 1
            # actual snowmelt computation
            flu.melt[k] = ((1. - d_minspeed ) * sta.gratio[k] + d_minspeed) * flu.potmelt[k]
            # snow pack updating
            sta.g[k] = sta.g[k] - flu.melt[k]
            # snow covered area updating
            if sta.g[k] < d_gthreshold:
                sta.gratio[k] = sta.g[k] / d_gthreshold
            else:
                sta.gratio[k] = 1

class Calc_SnowPack_V2(modeltools.Method):
    """ Calculate snow accumulation for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip(83., 83., 83., 83., 83.)
        >>> cn1(0.962)
        >>> cn2(2.249)
        >>> cn3(100.)
        >>> cn4(0.4)
        >>> derived.gthresh.update()
        >>> fluxes.tlayer =  -0.22318, -0.67402, -1.17348, -1.77018, -2.63208
        >>> fluxes.psnowlayer =  0.07273111, 0.086444894,  0.09857770,  0.10418780,  0.11285966
        >>> states.g = 0., 0., 0., 0., 0.
        >>> states.etg = 0., 0., 0., 0., 0.
        >>> states.gratio = 0., 0., 0., 0., 0.
        >>> states.glocalmax = derived.gthresh
        >>> model.calc_snowpack_v2()
        >>> states.g
        g(0.072731, 0.086445, 0.098578, 0.104188, 0.11286)
        >>> states.etg
        etg(-0.008481, -0.025613, -0.044592, -0.067267, -0.100019)
        >>> states.gratio
        gratio(0.000727, 0.000864, 0.000986, 0.001042, 0.001129)
        >>> fluxes.potmelt
        potmelt(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0)

        New Input data

        >>> fluxes.tlayer = 2.18124, 1.72836, 1.22664, 0.62724, -0.23856
        >>> fluxes.psnowlayer = 0.03695066, 0.059840058, 0.08740688, 0.12360633, 0.18275139
        >>> model.calc_snowpack_v2()
        >>> states.g
        g(0.098387, 0.131076, 0.166448, 0.227794, 0.295611)
        >>> states.etg
        etg(0.0, 0.0, 0.0, -0.040876, -0.105284)
        >>> states.gratio
        gratio(0.00356, 0.004852, 0.006281, 0.002278, 0.002956)
        >>> fluxes.potmelt
        potmelt(0.109682, 0.146285, 0.185985, 0.0, 0.0)
        >>> fluxes.melt
        melt(0.011294, 0.015209, 0.019536, 0.0, 0.0)

        New Input data

        >>> fluxes.tlayer = 3.58345, 3.12955, 2.62670, 2.02595, 1.15820
        >>> fluxes.psnowlayer = 0., 0., 0.26679315, 0.73575994, 1.50702064

        >>> model.calc_snowpack_v2()
        >>> states.g
        g(0.088286, 0.117503, 0.384829, 0.84203, 1.802632)
        >>> states.etg
        etg(0.0, 0.0, 0.0, 0.0, -0.057271)
        >>> states.gratio
        gratio(0.002659, 0.003539, 0.015233, 0.035165, 0.018026)
        >>> fluxes.potmelt
        potmelt(0.098387, 0.131076, 0.433242, 0.963554, 0.0)
        >>> fluxes.melt
        melt(0.010101, 0.013573, 0.048412, 0.121524, 0.0)
    """

    CONTROLPARAMETERS = (
        grxjland_control.NSnowLayers,
        grxjland_control.MeanAnSolidPrecip,
        grxjland_control.CN1,
        grxjland_control.CN2,
        grxjland_control.CN3,
        grxjland_control.CN4,
    )

    DERIVEDPARAMETERS = (
        grxjland_derived.GThresh,
    )

    REQUIREDSEQUENCES = (
        grxjland_fluxes.TLayer,
        grxjland_fluxes.PSnowLayer,
    )
    UPDATEDSEQUENCES = (
        grxjland_states.G,
        grxjland_states.ETG,
        grxjland_states.GLocalMax,
        grxjland_states.GRatio,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.PotMelt,
        grxjland_fluxes.Melt,

    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        d_tmelt = 0.
        d_minspeed = 0.1

        for k in range(con.nsnowlayers):
            if sta.glocalmax[k] == 0.:
                sta.glocalmax[k] = der.gthresh[k]
            d_ginit = sta.g[k]
            # update snow pack
            sta.g[k] = sta.g[k] + flu.psnowlayer[k]
            # thermal state before melt
            sta.etg[k] = min(0, con.cn1 * sta.etg[k] + (1. - con.cn1) * flu.tlayer[k])
            #potential melt
            if sta.etg[k] == 0 and flu.tlayer[k] > 0:
                flu.potmelt[k] = min(sta.g[k], con.cn2 * (flu.tlayer[k] - d_tmelt))
            else:
                flu.potmelt[k] = 0
            # snow covered area computation
            if flu.potmelt[k] > 0:
                if sta.g[k] < sta.glocalmax[k] and sta.gratio[k] == 1.:
                    sta.glocalmax[k] = sta.g[k]
                sta.gratio[k] = min(sta.g[k] / sta.glocalmax[k], 1.)


            # actual snowmelt computation
            flu.melt[k] = ((1. - d_minspeed ) * sta.gratio[k] + d_minspeed) * flu.potmelt[k]
            # snow pack updating
            sta.g[k] = sta.g[k] - flu.melt[k]
            d_dg = sta.g[k] - d_ginit
            if d_dg  > 0:
                sta.gratio[k] = min(sta.gratio[k] + (flu.psnowlayer[k] - flu.melt[k]) / con.cn3, 1.)
                if sta.gratio[k] == 1:
                    sta.glocalmax[k] = der.gthresh[k]
            if d_dg < 0:
                sta.gratio[k]  = min(sta.g[k]/sta.glocalmax[k], 1.)



class Calc_NetRainfall_V1(modeltools.Method):
    """ Calculate net rainfall and net evapotranspiration capacity.

    Basic equations:
    
        Determination of net rainfall and PE by subtracting E from P to determine either a net rainfall Pn or a net evapotranspiration capacity En:
    
      :math:`Pn = P - E, En = 0 \\ | \\ P \\geq E`
      
      :math:`Pn = 0,  En = E - P\\ | \\ P < E``

    Examples:
        
        Evapotranspiration larger than precipitation:
        
        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> inputs.p = 20.
        >>> inputs.e = 30.
        >>> model.calc_netrainfall_v1()
        >>> fluxes.en
        en(10.0)
        >>> fluxes.pn
        pn(0.0)
        >>> fluxes.ae
        ae(20.0)
        
        Precipitation larger than evapotranspiration:

        >>> inputs.p = 50.
        >>> inputs.e = 10.
        >>> model.calc_netrainfall_v1()
        >>> fluxes.en
        en(0.0)
        >>> fluxes.pn
        pn(40.0)
        >>> fluxes.ae
        ae(10.0)
    
    """
    
    REQUIREDSEQUENCES = (
        grxjland_inputs.P,
        grxjland_inputs.E,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Pn,
        grxjland_fluxes.En,
        grxjland_fluxes.AE,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        
        if inp.p >= inp.e:
            flu.pn = inp.p - inp.e
            flu.en = 0.
        else:
            flu.pn = 0.
            flu.en = inp.e - inp.p
        flu.ae = inp.e - flu.en


class Calc_NetRainfall_V2(modeltools.Method):
    """ Calculate net rainfall and net evapotranspiration capacity from liquid rainfall and snowmelt from CemaNeige SnowModule.

    Basic equations:

        Determination of net rainfall and PE by subtracting E from P to determine either a net rainfall Pn or a net evapotranspiration capacity En:

      :math:`Pn = P - E, En = 0 \\ | \\ P \\geq E`

      :math:`Pn = 0,  En = E - P\\ | \\ P < E``

    Examples:

        Evapotranspiration larger than precipitation:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> inputs.p = 20.
        >>> inputs.e = 30.
        >>> model.calc_netrainfall_v1()
        >>> fluxes.en
        en(10.0)
        >>> fluxes.pn
        pn(0.0)
        >>> fluxes.ae
        ae(20.0)

        Precipitation larger than evapotranspiration:

        >>> inputs.p = 50.
        >>> inputs.e = 10.
        >>> model.calc_netrainfall_v1()
        >>> fluxes.en
        en(0.0)
        >>> fluxes.pn
        pn(40.0)
        >>> fluxes.ae
        ae(10.0)

    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.PRainLayer,
        grxjland_fluxes.Melt,
        grxjland_inputs.E,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Pn,
        grxjland_fluxes.En,
        grxjland_fluxes.AE,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        # d_p = sum(flu.prainlayer) / len(flu.prainlayer) + sum(flu.melt) / len(flu.melt)
        d_p = 0
        for k in range(len(flu.melt)):
            d_p = flu.prainlayer[k]  / len(flu.prainlayer) + flu.melt[k] / len(flu.melt)

        if d_p >= inp.e:
            flu.pn = d_p - inp.e
            flu.en = 0.
        else:
            flu.pn = 0.
            flu.en = inp.e - d_p
        flu.ae = inp.e - flu.en
            

class Calc_InflowProductionStore_V1(modeltools.Method):
    """ Calculate part of net rainfall filling the production store.

    Basic equation:
    
        In case Pn is not zero, a part Ps of Pn fills the production store. It is determined as a function of the level S in the store by:
    
      :math:`Ps = \\frac{X1(1-(\\frac{S}{X1}^{2}tanh(\\frac{Pn}{X1}){1+\\frac{S}{X1}tanh(\\frac{Pn}{X1})}`

    Examples:
        
        Example production store full, no rain fills the production store
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x1(300)
        >>> states.s = 300
        >>> fluxes.pn = 50
        >>> model.calc_inflowproductionstore_v1()
        >>> fluxes.ps
        ps(0.0)
        
        Example routing store empty, nearly all net rainfall fills the production store:
        
        >>> states.s = 0
        >>> model.calc_inflowproductionstore_v1()
        >>> fluxes.ps
        ps(49.542124)
        
        Example no net rainfall:
        
        >>> fluxes.pn = 0
        >>> model.calc_inflowproductionstore_v1()
        >>> fluxes.ps
        ps(0.0)
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Pn,
        grxjland_states.S,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X1,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Ps,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        
        flu.ps = con.x1 * (1. - (sta.s / con.x1) ** 2.) * modelutils.tanh(flu.pn / con.x1) / (1. + sta.s / con.x1 * modelutils.tanh(flu.pn / con.x1))
        
class Calc_ProductionStore_V1(modeltools.Method):
    """ Calculate actual evaporation rate, water content and percolation leakage from the production store.

    Basic equations:
    
        Actual evaporation rate is determined as a function of the level in the production store to calculate the quantity 
        Es of water that will evaporate from the store. It is obtained by:
    
      :math:`Es = \\frac{S(2-\\frac{S}{X1}tanh(\\frac{En}{X1})}{1+(1-\\frac{S}{X1})tanh(\\frac{En}{X1})}`
      
        The water content in the production store is then updated with:
      
      :math:`S = S - Es + Ps`
      
        A percolation leakage Perc from the production store is then calculated as a power function of the reservoir content:
        
      :math:`Perc = S{1-[1+(\\frac{4 S}{9 X1})^{4}]^{-1/4}}`
      
        The reservoir content becomes:
        
      :math:`S = S- Perc`
      
        Calculate the total actual evapotranspiration from production storage and net rainfall calculation
        
      :math:`AE = Es + AE`

    Examples:
        
        Example production store nearly full, no rain:
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x1(300.)
        >>> fluxes.ps = 0.
        >>> fluxes.e = 10.
        >>> fluxes.en = 2.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 270.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(1.978652)
        >>> fluxes.ae
        ae(9.978652)
        >>> fluxes.perc
        perc(1.6402)
        >>> states.s
        s(266.381148)
        
        Check water balance:
        
        >>> 270. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0
        
        Example production store nearly full, rain:
        
        >>> fluxes.ps = 25.
        >>> fluxes.e = 10.
        >>> fluxes.en = 0.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 270.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(10.0)
        >>> fluxes.perc
        perc(2.630796)
        >>> states.s
        s(292.369204)
        
        Check water balance:
        
        >>> 270. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0
        
        Example production store empty, no rain
        
        >>> fluxes.ps = 0.
        >>> fluxes.e = 10.
        >>> fluxes.en = 2.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 0.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(8.0)
        >>> fluxes.perc
        perc(0.0)
        >>> states.s
        s(0.0)
        
        Example production store empty, rain
        
        >>> fluxes.ps = 30.
        >>> fluxes.e = 10.
        >>> fluxes.en = 0.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 0.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(10.0)
        >>> fluxes.perc
        perc(0.000029)
        >>> states.s
        s(29.999971)
        
        Check water balance:
        
        >>> 0. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Ps,
        grxjland_fluxes.En,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X1,
    )

    UPDATEDSEQUENCES = (
        grxjland_states.S,
        grxjland_fluxes.AE,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Es,
        grxjland_fluxes.Perc,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.es = (sta.s * (2. - sta.s / con.x1) * modelutils.tanh(flu.en / con.x1)) / (1. + (1. - sta.s / con.x1) * modelutils.tanh(flu.en / con.x1))
        sta.s = sta.s - flu.es + flu.ps
        # flu.perc = sta.s * (1. - (1. + (4. * sta.s / 9. / con.x1) ** 4.) ** (-0.25))
        # probably faster
        flu.perc = sta.s * (1. - (1. + (sta.s / con.x1) ** 4. / 25.62890625) ** (-0.25)) 
        sta.s = sta.s - flu.perc
        flu.ae = flu.ae + flu.es
        

class Calc_Pr_V1(modeltools.Method):
    """ Total quantity Pr of water reaching the routing functions.
    
    

    Basic equation:
    
      :math:`Pr = Perc + (Pn - Ps)`

    Examples:
        
        Example production store nearly full, no rain:
        
        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.ps = 3.
        >>> fluxes.perc = 10.
        >>> fluxes.pn = 5.
        >>> model.calc_pr_v1()
        >>> 
        >>> fluxes.pr
        pr(12.0)
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Ps,
        grxjland_fluxes.Pn,
        grxjland_fluxes.Perc,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Pr,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr = flu.perc + flu.pn - flu.ps
    

class Calc_UH1_V1(modeltools.Method):
    """Calculate the unit hydrograph UH1 output (convolution).
    
    Input to the unit hydrograph UH1 is 90% of Pr.

    Examples:

        Prepare a unit hydrograph with only three ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(3)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(0.06415, 0.298737, 0.637113)
        >>> logs.quh1 = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pr = 0.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(1.0)
        >>> logs.quh1
        quh1(3.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(3.23094)
        >>> logs.quh1
        quh1(1.075454, 2.293605, 0.0)
        
        In the next example we set the memory to zero (no input in the past), and apply a single input signal:
        
        >>> logs.quh1 = 0.0, 0.0, 0.0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(0.23094)
        >>> fluxes.pr = 0.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(1.075454)
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(2.293605)
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(0.0)
        
        A unit hydrograph with only one ordinate results in the direct
        routing of the input, remember, only 90% of pr enters UH1:
        
        >>> x4(0.8)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(1.0)
        >>> logs.quh1 = 0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(3.6)
        
    """
    DERIVEDPARAMETERS = (
        grxjland_derived.UH1,
    )
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Pr,
    )
    UPDATEDSEQUENCES = (
        grxjland_logs.QUH1,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Q9,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        # 90 % of Pr enters UH1
        flu.q9 = der.uh1[0] * 0.9 * flu.pr + log.quh1[0]
        for jdx in range(1, len(der.uh1)):
            log.quh1[jdx - 1] = der.uh1[jdx] * 0.9 * flu.pr + log.quh1[jdx]
            
class Calc_UH2_V1(modeltools.Method):
    """Calculate the unit hydrograph UH2 output (convolution).
    
    Input to the unit hydrograph UH2 is 10% of Pr.

    Examples:

        Prepare a unit hydrograph with six ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 1.0, 3.0, 0.0, 2.0, 1.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(1.0)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 1.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pr = 4.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(3.01283)
        >>> logs.quh2
        quh2(0.059747, 2.127423, 1.127423, 0.059747, 0.01283, 0.0)
        
        In the next example we set the memory to zero (no input in the past), and apply a single input signal:
        
        >>> logs.quh2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.0)
        
    """
    DERIVEDPARAMETERS = (
        grxjland_derived.UH2,
    )
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Pr,
    )
    UPDATEDSEQUENCES = (
        grxjland_logs.QUH2,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Q1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        # 10 % of Pr enters UH2
        flu.q1 = der.uh2[0] * 0.1 * flu.pr + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * 0.1 * flu.pr + log.quh2[jdx]
            

class Calc_UH2_V2(modeltools.Method):
    """Calculate the unit hydrograph UH2 output (convolution).
    
    This is the version for the GR5J model. The input is 100% of Pr, the output of the Unit Hydrograph is 
    splitted in two parts: 90% gets Q9 and 10% gets Q1.

    Examples:

        Prepare a unit hydrograph with only six ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 3.0, 3.0, 0.0, 2.0, 4.0, 0.0
        
        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left. The output is splitted in the two parts:
        
        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v2()
        >>> fluxes.q1
        q1(0.3)
        >>> fluxes.q9
        q9(2.7)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 4.0, 0.0, 0.0)
        
    """
    DERIVEDPARAMETERS = (
        grxjland_derived.UH2,
    )
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Pr,
    )
    UPDATEDSEQUENCES = (
        grxjland_logs.QUH2,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Q1,
        grxjland_fluxes.Q9,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        d_quh2 = der.uh2[0] * flu.pr + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * flu.pr + log.quh2[jdx]
        flu.q1 = 0.1 * d_quh2
        flu.q9 = 0.9 * d_quh2

            
class Calc_RoutingStore_V1(modeltools.Method):
    """ Calculate groundwater exchange term F, level of the non-linear routing store R and the outflow Qr of the reservoir.

    Basic equations:
    
        The ground waterexchange term F that acts on both flow components is calculated as:
        
      :math:`F = X2 \\frac{R}{X3}^{7/2}`
      
      
        X2 is the water exchange coefficient. X2 can be either positive in case of water imports, negative for water exports or zero when there is no water exchange.
        The  higher the level in the routing store, the larger the  exchange.
       
        The level in the routing store is updated by adding the output Q9 of UH1 and F:
      
      :math:`R = max(0; R + Q9 + F)`
      
        The outflow Qr of the reservoir is then calculated as:
        
      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`
      
        The level in the reservoir becomes:
      
      :math:`R = R - Qr`
      

    Examples:
        
        Positive groundwater exchange coefficient, routing storage nearly full
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(1.02)
        >>> x3(100.)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(0.852379)
        >>> states.r
        r(89.548769)
        >>> fluxes.qr
        qr(26.30361)
        
        Positive groundwater exchange coefficient, routing storage nearly empty:
        
        >>> states.r = 10.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(0.000323)
        >>> states.r
        r(29.939875)
        >>> fluxes.qr
        qr(0.060448)
        
        Negative groundwater exchange coefficient, routing storage nearly full
        
        >>> x2(-1.02)
        >>> states.r = 95.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(-0.852379)
        >>> states.r
        r(89.067124)
        >>> fluxes.qr
        qr(25.080497)
        
        Negative groundwater exchange coefficient, routing storage nearly empty:
        
        >>> states.r = 10.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(-0.000323)
        >>> states.r
        r(29.939236)
        >>> fluxes.qr
        qr(0.060441)
        
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q9,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
    )

    UPDATEDSEQUENCES = (
        grxjland_states.R,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3) ** 3.5
        sta.r = max(0, sta.r + flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r/con.x3)**4)**(-0.25))
        sta.r = sta.r - flu.qr
        
class Calc_RoutingStore_V2(modeltools.Method):
    """ Calculate groundwater exchange term F, level of the non-linear routing store R and the outflow Qr of the reservoir.
    
    This is the GR5J version of the routing store.

    Basic equations:
    
        The ground water exchange term F that acts on both flow components is calculated as:
        
      :math:`F = X2 (\\frac{R}{X3} - X5)`
      
      
        X2 is the water exchange coefficient. X2 can be either positive in case of water imports, negative for water exports or zero when there is no water exchange.
        The  higher the level in the routing store, the larger the  exchange. X5 can be seen as the external, quasi-stationary potential of the groundwater system
        and F is a ‘‘restoring flux’’ acting like a spring device with constant X2. Usually, X2 is negative: the more R/X3 de-parts from X5, the more intense the flux is,
        which tends to restore its value to X5.
       
        The level in the routing store is updated by adding the output Q9 of UH1 and F:
      
      :math:`R = max(0; R + Q9 + F)`
      
        The outflow Qr of the reservoir is then calculated as:
        
      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`
      
        The level in the reservoir becomes:
      
      :math:`R = R - Qr`
      

    Examples:
        
        Filled storage
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v2()
        >>> fluxes.f
        f(-0.137898)
        >>> states.r
        r(89.271754)
        >>> fluxes.qr
        qr(25.590348)
        
        Empty storage:
        
        >>> states.r = 10.
        >>> model.calc_routingstore_v2()
        >>> fluxes.f
        f(0.000652)
        >>> states.r
        r(29.940201)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q9,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
        grxjland_control.X5,
    )

    UPDATEDSEQUENCES = (
        grxjland_states.R,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3 - con.x5)
        sta.r = max(0, sta.r + flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r/con.x3)**4)**(-0.25))
        sta.r = sta.r - flu.qr
        

class Calc_RoutingStore_V3(modeltools.Method):
    """ Calculate groundwater exchange term F, level of the non-linear routing store R and the outflow Qr of the reservoir.
    
    This is the GR6J version of the routing store. 60 % of Q9 enters the routing store.

    Basic equations:
    
        The ground water exchange term F that acts on both flow components is calculated as:
        
      :math:`F = X2 (\\frac{R}{X3} - X5)`
      
      
        X2 is the water exchange coefficient. X2 can be either positive in case of water imports, negative for water exports or zero when there is no water exchange.
        The  higher the level in the routing store, the larger the  exchange. X5 can be seen as the external, quasi-stationary potential of the groundwater system
        and F is a ‘‘restoring flux’’ acting like a spring device with constant X2. Usually, X2 is negative: the more R/X3 de-parts from X5, the more intense the flux is,
        which tends to restore its value to X5.
       
        The level in the routing store is updated by adding the output Q9 of UH1 and F:
      
      :math:`R = max(0; R + Q9 + F)`
      
        The outflow Qr of the reservoir is then calculated as:
        
      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`
      
        The level in the reservoir becomes:
      
      :math:`R = R - Qr`
      

    Examples:
        
        Filled storage
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v3()
        >>> fluxes.f
        f(-0.137898)
        >>> states.r
        r(86.736252)
        >>> fluxes.qr
        qr(20.12585)
        
        Empty storage:
        
        >>> states.r = 10.
        >>> model.calc_routingstore_v3()
        >>> fluxes.f
        f(0.000652)
        >>> states.r
        r(21.987785)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q9,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
        grxjland_control.X5,
    )

    UPDATEDSEQUENCES = (
        grxjland_states.R,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3 - con.x5)
        sta.r = max(0, sta.r + 0.6 * flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r/con.x3)**4)**(-0.25))
        sta.r = sta.r - flu.qr
        
        
class Calc_ExponentialStore_V3(modeltools.Method):
    """ Calculate exponential store.
    
    This is the exponential store of the GR6J version. 40 % of Q9 enters the routing store.

    Basic equations:
    
    TODO
      

    Examples:
        
        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x6(4.5)
        >>> fluxes.q9 = 10.
        >>> fluxes.f = -0.5
        >>> states.r2 = 40.
        >>> model.calc_exponentialstore_v3()
        >>> states.r2
        r2(-0.000285)
        >>> fluxes.qr2
        qr2(43.500285)
        
        Negative storage values possible
        
        >>> states.r2 = -10.
        >>> fluxes.q9 = 0.1
        >>> model.calc_exponentialstore_v3()
        >>> states.r2
        r2(-10.880042)
        >>> fluxes.qr2
        qr2(0.420042)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q9,
        grxjland_fluxes.F,
    )
    CONTROLPARAMETERS = (
        grxjland_control.X6,
    )

    UPDATEDSEQUENCES = (
        grxjland_states.R2,
    )
    
    RESULTSEQUENCES = (

        grxjland_fluxes.Qr2,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        sta.r2 = sta.r2 + 0.4 * flu.q9 + flu.f
        d_ar = sta.r2 / con.x6
        if d_ar > 33.:
            d_ar = 33.
        elif d_ar < -33.:
            d_ar = -33.
        
        if d_ar > 7:
            flu.qr2 = sta.r2 + con.x6 / modelutils.exp(d_ar)
        elif d_ar < -7:
            flu.qr2 = con.x6 * modelutils.exp(d_ar)
        else:
            flu.qr2 = con.x6*modelutils.log(modelutils.exp(d_ar) + 1.)
        
        sta.r2 = sta.r2 - flu.qr2


class Calc_Qd_V1(modeltools.Method):
    """ Calculate direct flow component.

    Basic equations:
    
        Output Q1 of unit hydrograph UH2 is subject to the same water exchange F as the routing storage to
        give the flow component as:
        
      :math:`Qd = max(0; Q1 + F)`
      
      
    Examples:
        
        Positive groundwater exchange: 
        
        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.q1 = 20
        >>> fluxes.f = 20
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(40.0)
        
        Negative groundwater exchange:
        
        >>> fluxes.f = -10
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(10.0)
        
        Negative groundwater exchange exceeding outflow of unit hydrograph:
        >>> fluxes.f = -30
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(0.0)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q1,
        grxjland_fluxes.F,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Qd,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qd = max(0, flu.q1 + flu.f)
        
class Calc_Qt_V1(modeltools.Method):
    """ Calculate total flow.

    Basic equations:
    
        Total streamflow is obtained by
    
      :math:`Qt = Qr + Qd`
    
      
    Examples:
        
        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20
        >>> fluxes.qd = 10
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(30.0)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Qr,
        grxjland_fluxes.Qd,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Qt,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qd
        
class Calc_Qt_V3(modeltools.Method):
    """ Calculate total flow.
    
    GR6jX model version

    Basic equations:
    
        Total streamflow is obtained by
    
      :math:`Qt = Qr + Qr2 + Qd`
    
      
    Examples:
        
        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20.
        >>> fluxes.qr2 = 10.
        >>> fluxes.qd = 10.
        >>> model.calc_qt_v3()
        >>> fluxes.qt
        qt(40.0)
        
    """
    
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Qr,
        grxjland_fluxes.Qr2,
        grxjland_fluxes.Qd,
    )
    
    RESULTSEQUENCES = (
        grxjland_fluxes.Qt,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qr2 + flu.qd
        
class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
      :math:`Q = QFactor \\cdot QT`
      
    
    """
    DERIVEDPARAMETERS = (
        grxjland_derived.QFactor,
    )
    REQUIREDSEQUENCES = (
        grxjland_fluxes.Qt,
    )
    RESULTSEQUENCES = (
        grxjland_outlets.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor*flu.qt


class Model(modeltools.AdHocModel):
    """The GRxJ-Land base model."""
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_PSnowLayer_V1,
        Calc_TSnowLayer_V1,
        Calc_TSnowLayer_V2,
        Calc_FracSolidPrec_V1,
        Calc_FracSolidPrec_V2,
        Calc_SnowPack_V1,
        Calc_SnowPack_V2,
        Calc_NetRainfall_V1,
        Calc_NetRainfall_V2,
        Calc_InflowProductionStore_V1,
        Calc_ProductionStore_V1,
        Calc_Pr_V1,
        Calc_UH1_V1,
        Calc_UH2_V1,
        Calc_UH2_V2,
        Calc_RoutingStore_V1,
        Calc_RoutingStore_V2,
        Calc_RoutingStore_V3,
        Calc_ExponentialStore_V3,
        Calc_Qd_V1,
        Calc_Qt_V1,
        Calc_Qt_V3,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (
        Pass_Q_V1,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
