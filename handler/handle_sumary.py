from typing import List, Dict, Optional, Union

from typing_extensions import Any

from function.make_summary import make_summary


def summarize_food_labels(
    data: Dict[str, Any]
) -> Optional[Dict[str, Union[None, str, List[Any]]]]:
    ingredients = data.get("ingredients", [])

    if not ingredients:
        return {
            "nama": None,
            "status": "",
            "detail": ""
        }

    names = [ing.get("nama", "") for ing in ingredients]
    nama = " ".join(word.capitalize() for word in names)

    print(data)
    summary = make_summary(data)

    return {
        "status": "success",
        "data": summary
    }