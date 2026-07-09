# -*- coding: utf-8 -*-
"""
Реестр генераторов — единая точка регистрации типов (см. skill mosgen-dev §1.1).
Движок и API работают с типами обобщённо через GENERATORS, не зная внутренностей модулей.
Новый тип = добавить импорт + строку в GENERATORS.
"""
from generators.akt_nachala import AktNachala
from generators.prikaz_ppu import PrikazPpu
from generators.polozhenie_ppu import PolozheniePpu
from generators.prikaz_comp_ppu import PrikazCompPpu
from generators.polozhenie_comp_ppu import PolozhenieCompPpu
from generators.prikaz_otvetstvennyh import PrikazOtvetstvennyh
from generators.prikaz_tirazh import PrikazTirazh
from generators.protokol_vypolneniya import ProtokolVypolneniya
from generators.prikaz_ic import PrikazIc

# doc_type -> класс генератора
GENERATORS = {
    AktNachala.DOC_TYPE: AktNachala,
    PrikazPpu.DOC_TYPE: PrikazPpu,
    PolozheniePpu.DOC_TYPE: PolozheniePpu,
    PrikazCompPpu.DOC_TYPE: PrikazCompPpu,
    PolozhenieCompPpu.DOC_TYPE: PolozhenieCompPpu,
    PrikazOtvetstvennyh.DOC_TYPE: PrikazOtvetstvennyh,
    PrikazTirazh.DOC_TYPE: PrikazTirazh,
    ProtokolVypolneniya.DOC_TYPE: ProtokolVypolneniya,
    PrikazIc.DOC_TYPE: PrikazIc,
}


def get_generator(doc_type: str):
    """вернуть экземпляр генератора по doc_type (или None)"""
    cls = GENERATORS.get(doc_type)
    return cls() if cls else None
