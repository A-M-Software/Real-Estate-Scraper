# coding=utf-8

import asyncio
from json import dump

from src.clients import OLXAPIClient

PHONES = {
    "0509668609": "Віталій",
    "0969321697": "Марина",
    "0981781539": "Жанна",
    "0990203039": "Марія",
    "0506284590": "Яна",
    "0684373635": "Віктор",
    "0508265466": "Артур",
    "0661369826": "Марина (Рекламне)",
    "0952224049": "Тетяна",
}


def fmt_phone(phone: str) -> str:
    """
    Format ukrainian phone number
    """

    if phone == "0508265456":
        # Fix phone
        phone = "0508265466"

    name = PHONES.get(phone, "<Невідомо>")

    if phone.startswith("0"):
        phone = "+38" + phone

    return f"**{name} {phone[:3]} ({phone[3:6]}) {phone[6:9]} {phone[9:11]} {phone[11:13]}**"


async def main() -> None:
    async with OLXAPIClient() as client:
        all_adverts = []
        offset = 0

        while True:
            adverts_data = await client.request_json(
                method="GET",
                url="/adverts",
                params={
                    "offset": offset,
                }
            )

            if adverts := adverts_data.get("data"):
                # Next page
                all_adverts.extend(adverts)
                offset += 100

            else:
                # No more adverts
                break

        with open("adverts.json", "w") as f:
            dump(all_adverts, f, indent=2, ensure_ascii=False)

        # sale_adverts = len([advert for advert in all_adverts if advert["category_id"] == 1758])
        # print(
        #     f"<b>Всього оголошень</b>"
        #     f"- Продаж: {sale_adverts}\n"
        #     f"- Оренда: {len(all_adverts) - sale_adverts}\n"
        # )

        # Filter only active
        all_adverts = [advert for advert in all_adverts if advert["status"] == "active"]
        sale_adverts = len([advert for advert in all_adverts if advert["category_id"] == 1758])

        print(
            f"**Всього активних оголошень**\n"
            f"- Продаж: {sale_adverts}\n"
            f"- Оренда: {len(all_adverts) - sale_adverts}\n"
        )

        data = {}

        for advert in all_adverts:
            if (phone := "".join(advert["contact"]["phone"].split())) not in data:
                # Not added yet
                data[phone] = []

            data[phone].append(advert)

        with open("adverts_by_phone.json", "w") as f:
            dump(data, f, indent=2, ensure_ascii=False)

        for phone, adverts in data.items():
            sale_adverts = len([advert for advert in adverts if advert["category_id"] == 1758])

            print(
                f"{fmt_phone(phone)}:\n"
                f"- Продаж: {sale_adverts}\n"
                f"- Оренда: {len(adverts) - sale_adverts}\n"
            )
            # for advert in adverts:
            #     print(f" - {advert['url']}")


if __name__ == "__main__":
    asyncio.run(main())
