from fastapi import APIRouter, Query
import requests
from fastapi import HTTPException

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/necessities-price")
def get_necessities_prices(
        category_name=Query(None), commodity_name=Query(None)
):
    """
    Retrieve the prices of necessities based on category and commodity name.

    :param category_name: The category name of the necessities to filter by.
    :param commodity_name: The commodity name of the necessities to filter by.
    :return: A JSON response containing the prices of the filtered necessities.
    """
    try:
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category_name, "Name": commodity_name},
        ).json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail="Failed to fetch prices from external source.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")