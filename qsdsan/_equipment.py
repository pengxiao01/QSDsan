#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
QSDsan: Quantitative Sustainable Design for sanitation and resource recovery systems

This module is developed by:
    Yalin Li <zoe.yalin.li@gmail.com>

This module is under the University of Illinois/NCSA Open Source License.
Please refer to https://github.com/QSD-Group/QSDsan/blob/main/LICENSE.txt
for license details.
'''


# %%

from biosteam.utils import NotImplementedMethod
from thermosteam.utils import registered
from .utils import (auom, register_with_prefix)

__all__ = ('Equipment',)

@registered(ticket_name='Equip')
class Equipment:
    '''
    A flexible class for the design of individual equipment of a :class:`SanUnit`,
    this class can be dependent on but will not affect the mass flows within
    the unit.

    A non-abstract subclass of this class must have:

        - A :func:`Equipment._design` method for equipment design.

            - This method should be called in the `_design` method of the unit \
            the equipment belongs to using :func:`SanUnit.add_equipment_design`.
            - It should return a dict that contains the design (e.g., dimensions) \
            of this equipment.
            - Unit (e.g., m, kg) of the design parameters should be stored in \
            the attribute `Equipment._units`.

        - A :func:`Equipment._cost` method for equipment cost.

            - This method should be called in the `_cost` method of the unit \
            the equipment belongs to using :func:`SanUnit.add_equipment_cost`.
            - It should return a float or a dict that contains \
            the total purchase cost of this equipment \
            (or the different parts of the equipment).
            - Installed cost (:math:`C_{BM}`) of this equipment will be caluculated \
            based on the purchase cost (:math:`C_{Pb}`)

                .. math::

                   C_{BM} = C_{Pb} (F_{BM} + F_{D}F_{P}F_{M} - 1)

    Parameters
    ----------
    ID : str
        ID of this equipment,
        a default ID will be given if not provided.
        If this equipment is linked to a unit,
        then the actual ID will be {unit.ID}_{ID}.
    linked_unit : obj
        Unit that this equipment is linked to, can be left as None.
    units: dict
        Units of measure (e.g., m, kg) the of design parameters.
    F_BM: float or dict(str, float)
        Bare module factor of this equipment.
    F_D: float or dict(str, float)
        Design factor of this equipment.
    F_P: float or dict(str, float)
        Pressure factor of this equipment.
    F_M: float or dict(str, float)
        Material factor of this equipment.
    lifetime: float or dict(str, float)
        Lifetime of this equipment.
    lifetime_unit: str
        Unit of the lifetime.
    '''

    def __init_subclass__(self, isabstract=False):
        if isabstract: return
        for method in ('_design', '_cost'):
            if not hasattr(self, method):
                raise NotImplementedError(
                    f'`Equipment` subclasses must have a {method} method unless `isabstract` is True.')

    _design = _cost = NotImplementedMethod

    def __init__(self, linked_unit=None, ID=None, units=dict(),
                 F_BM=1., F_D=1., F_P=1., F_M=1.,
                 lifetime=None, lifetime_unit='yr', **kwargs):

        if 'BM' in kwargs.keys():
            raise DeprecationWarning('`BM` has been depreciated, please use ' \
                                     f'`F_BM` for the Equipment {ID}.')
        self._linked_unit = linked_unit
        prefix = linked_unit.ID if linked_unit else ''
        register_with_prefix(self, prefix, ID)
        self._units = units
        self.F_BM = F_BM
        self.F_D = F_D
        self.F_P = F_P
        self.F_M = F_M
        if isinstance(lifetime, dict):
            equip_lifetime = {}
            for k, v in lifetime:
                equip_lifetime[v] = auom(lifetime_unit).convert(v, 'yr')
        else:
            equip_lifetime = auom(lifetime_unit).convert(lifetime, 'yr')
        self.lifetime = equip_lifetime

    def __repr__(self):
        return f'<Equipment: {self.ID}>'

    @property
    def linked_unit(self):
        '''
        :class:`~.SanUnit` The unit that this equipment belongs to.

        .. note::

            This property will be updated upon initialization of the unit.
        '''
        return self._linked_unit

    @property
    def design(self):
        '''[dict] Design information generated by :func:`Equipment._design`.'''
        return self._design()

    @property
    def units(self):
        '''[dict] Units of measure (e.g., m, kg) the of design parameters.'''
        return self._units

    @property
    def purchase_cost(self):
        '''[float] Total purchase cost generated by :func:`Equipment._cost`.'''
        return self._cost()

    @property
    def installed_cost(self):
        '''[float] Total installed cost based on purchase cost and bare module factor.'''
        return self.purchase_cost*(self.F_BM+self.F_D*self.F_P*self.F_M-1)