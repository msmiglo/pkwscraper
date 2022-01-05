
"""
EXPLANATION OF TERRITORY CODES:

EN:
- Code for commune has 6 digits:
    * 2 for voivodship,
    * 2 for district,
    * 2 for commune.
- Zero does not count - 00 on the end means this is whole district
      code, and 0000 at the end means this is whole voivodship code.
- Voivodships ("województwo") numbers are even, that is from 2 to 32.
- Leading zero can be omitted for voivodships from 02 to 08.
- Districts ("powiat") have numbers from 01 up.
- Cities with the district status ("powiat grodzki") have numbers from
      61 up, but some may be skipped by one.
- Communes ("gmina") have numbers from 01 up every 1.
- Among cities with the district status, only Warsaw has city-districts
      ("dzielnica") as communes, but the number 01 is reserved so they
      have number from 02 to 19.
- Warsaw as a district has code 14 65 01, so it is strange, because it
      should have 14 65.
- 14 99 01 is a code for abroad.


PL (WYTŁUMACZENIE KODÓW TERYTORIALNYCH):
- Numer gminy to 6 cyfr:
    * 2 na województwo,
    * 2 na powiat,
    * 2 na gminę.
- Zero się nie liczy - gdy na końcu jest 00 to znaczy, że jest to kod
      całego powiatu, jeśli na końcu jest 0000 to jest to kod całego
      województwa.
- Województwo ma numery parzyste, czyli od 2 do 32.
- Zero z przodu może być pominięte dla województw od 02 do 08.
- Powiaty mają numer od 01 w górę.
- Powiaty grodzkie mają numery od 61 w górę, ale może przeskoczyć o jedno.
- Gminy mają numery od 01 w górę co 1.
- Z powiatów grodzkich tylko Warszawa ma dzielnice jako gminy,
      ale są numerowane bez numerka 01, czyli jest od 02 do 19.
- Warszawa jako powiat ma kod 14 65 01, więc w ogóle dziwnie,
      bo powinna mieć 14 65 00.
- 14 99 01 to kod dla zagranicy.
"""

def get_parent_code(code):
    if isinstance(code, str):
        return _get_parent_code_str(code)
    elif isinstance(code, int):
        return _get_parent_code_int(code)
    else:
        raise TypeError(f"Expected type `int` or `str`, got: {type(code)}.")


def _get_parent_code_int(code_int):
    voivod_code = code_int // 10000
    if voivod_code % 2 == 1 or not (0 < voivod_code <= 32):
        raise ValueError(f'Wrong voivodship prefix value: {code_int}.')
    if code_int == 149901:
        return 146501
    if code_int == 146501:
        return 140000
    if code_int // 100 == 1465:
        return 146501
    if code_int % 10000 == 0:
        raise ValueError("Voivodships do not have parents.")
    if code_int % 100 == 0:
        return 10000 * (code_int // 10000)
    if code_int % 1 == 0:
        return 100 * (code_int // 100)
    raise ValueError(f'Wrong code format: {code_int}.')


def _get_parent_code_str(code_str):
    code_int = int(code_str)
    parent_int = _get_parent_code_int(code_int)
    parent_str = str(parent_int)
    return parent_str
