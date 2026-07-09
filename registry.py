# -*- coding: utf-8 -*-
"""
Реестр генераторов — единая точка регистрации типов (см. skill mosgen-dev §1.1).
Движок и API работают с типами обобщённо через GENERATORS, не зная внутренностей модулей.
Новый тип = добавить импорт + строку в GENERATORS.
"""
from generators.akt_nachala import AktNachala
from generators.prikaz_ppu import PrikazPpu
from generators.polozhenie_ppu import PolozheniePpu

# doc_type -> класс генератора
GENERATORS = {
    AktNachala.DOC_TYPE: AktNachala,
    PrikazPpu.DOC_TYPE: PrikazPpu,
    PolozheniePpu.DOC_TYPE: PolozheniePpu,
}


def get_generator(doc_type: str):
    """вернуть экземпляр генератора по doc_type (или None)"""
    cls = GENERATORS.get(doc_type)
    return cls() if cls else None
