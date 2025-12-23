from dataclasses import dataclass
from typing import Optional, Dict, List
from typing import Dict, List


product_rank = {
    "mtpl": 1,
    "limited_casco": 2,
    "casco": 3,
}

variants_rank = {
    "compact": 1,
    "basic": 1,
    "comfort": 2,
    "premium": 3,
}

deductables_rank = {
    100: 1,
    200: 2,
    500: 3,
}

core_product = {"mtpl"}


def get_product_rank(product: str) -> int:
    try:
        return product_rank[product]
    except KeyError as e:
        raise KeyError(f"Unknown product key: {product!r}") from e


def get_variant_rank(variant: str) -> int:
    try:
        return variants_rank[variant]
    except KeyError as e:
        raise KeyError(f"Unknown variant key: {variant!r}") from e


def get_deductible_rank(deductible: int) -> int:
    try:
        return deductables_rank[deductible]
    except KeyError as e:
        raise KeyError(f"Unknown deductible key: {deductible!r}") from e


@dataclass
class PriceElement:
    key: str
    product: str
    variant: Optional[str] = None
    deductible: Optional[int] = None


def parse_price_key(input_key: str) -> PriceElement:
    parts = input_key.split("_")

    if parts[:2] == ["limited", "casco"] and len(parts) == 4:
        product = "limited_casco"
        variant = parts[2]
        deductible = int(parts[3])
        return PriceElement(key=input_key, product=product, variant=variant, deductible=deductible)

    if len(parts) == 3:
        product = parts[0]
        variant = parts[1]
        deductible = int(parts[2])
        return PriceElement(key=input_key, product=product, variant=variant, deductible=deductible)

    raise ValueError(f"Unrecognized key format: {input_key!r}")


def build_price_items(prices: Dict[str, int]) -> List[PriceElement]:
    items: List[PriceElement] = []

    for input_key, price in prices.items():
        if input_key in core_product:
            items.append(PriceElement(key=input_key, product=input_key, variant=None, deductible=None))
        else:
            items.append(parse_price_key(input_key))

    return items


def detect_inconsistencies(items: List[PriceElement], prices: Dict[str, int]) -> str:
    report: List[str] = []

    n = len(items)
    for i in range(n):
        for j in range(i + 1, n):
            a = items[i]
            b = items[j]

            price_a = prices[a.key]
            price_b = prices[b.key]

            pa = get_product_rank(a.product)
            pb = get_product_rank(b.product)

            if pa != pb:
                lower, higher = (a, b) if pa < pb else (b, a)
                lower_price = price_a if lower is a else price_b
                higher_price = price_b if higher is b else price_a

                if lower.product in core_product and lower_price >= higher_price:
                    report.append(
                        f"PRODUCT ORDER: '{lower.key}' ({lower_price}) should be cheaper than '{higher.key}' ({higher_price})."
                    )

            if (
                a.product != b.product
                and a.product not in core_product
                and b.product not in core_product
                and a.variant == b.variant
                and a.deductible == b.deductible
            ):
                pa = get_product_rank(a.product)
                pb = get_product_rank(b.product)

                lower_p, higher_p = (a, b) if pa < pb else (b, a)
                lower_price = price_a if lower_p is a else price_b
                higher_price = price_b if higher_p is b else price_a

                if lower_price >= higher_price:
                    report.append(
                        f"PRODUCT ORDER (same variant+deductible): '{lower_p.key}' ({lower_price}) should be cheaper than '{higher_p.key}' ({higher_price})."
                    )

            if (
                a.product == b.product
                and a.product not in core_product
                and b.product not in core_product
                and a.deductible == b.deductible
                
            ):
                va = get_variant_rank(a.variant)
                vb = get_variant_rank(b.variant)

                if va != vb:
                    lower_v, higher_v = (a, b) if va < vb else (b, a)
                    lower_price = price_a if lower_v is a else price_b
                    higher_price = price_b if higher_v is b else price_a

                    if lower_price >= higher_price:
                        report.append(
                            f"VARIANT ORDER: '{lower_v.key}' ({lower_price}) should be cheaper than '{higher_v.key}' ({higher_price})."
                        )

            if (
                a.product == b.product
                and a.product not in core_product
                and b.product not in core_product
                and a.variant == b.variant
            ):
                da = get_deductible_rank(a.deductible)
                db = get_deductible_rank(b.deductible)

                if da != db:
                    lower_d, higher_d = (a, b) if da < db else (b, a)
                    lower_price = price_a if lower_d is a else price_b
                    higher_price = price_b if higher_d is b else price_a

                    if higher_price >= lower_price:
                        report.append(
                            f"DEDUCTIBLE ORDER: '{higher_d.key}' ({higher_price}) should be cheaper than '{lower_d.key}' ({lower_price})."
                        )

    return "\n".join(report)





def fix_products_inplace(
    items: List[PriceElement],
    prices: Dict[str, int],
    avg_prices: Dict[str, float],
    max_iters: int = 10,
) -> None:
    for _ in range(max_iters):
        changed = False
        n = len(items)

        for i in range(n):
            for j in range(i + 1, n):
                a = items[i]
                b = items[j]

                pa = get_product_rank(a.product)
                pb = get_product_rank(b.product)

                va = None if (a.product in core_product) else get_variant_rank(a.variant)  
                vb = None if (b.product in core_product) else get_variant_rank(b.variant) 

                da = None if (a.product in core_product) else get_deductible_rank(a.deductible) 
                db = None if (b.product in core_product) else get_deductible_rank(b.deductible)  

                if pa != pb:
                    lower, higher = (a, b) if pa < pb else (b, a)

                    lower_is_core = lower.product in core_product
                    higher_is_core = higher.product in core_product

                    lower_price = prices[lower.key]
                    higher_price = prices[higher.key]

                    avg_low = avg_prices.get(lower.product)
                    avg_high = avg_prices.get(higher.product)

                           
                    ratio = avg_high / avg_low

                    if lower_price >= higher_price:
                        # CASE 1: non-core vs non-core + isti variant & deductible
                        if (not lower_is_core) and (not higher_is_core) and  lower.variant == higher.variant and lower.deductible == higher.deductible :
                            old_h = prices[higher.key]
                            new_h = int(round(lower_price * ratio))    
                            factor = new_h / old_h
                            prices[higher.key] =  new_h

                        
                        # CASE 2: lower je core, higher nije core
                        if (lower.product in core_product) and (higher.product not in core_product):
                           
                            old_min = None
                            for it in items:
                                if it.product == higher.product:
                                    p = prices[it.key]
                                    old_min = p if old_min is None else min(old_min, p)

                            new_min = int(round(lower_price * ratio))
                            factor = new_min / old_min

                            for it in items:
                                if it.product == higher.product:
                                    new_val = int(round(prices[it.key] * factor))
                                    prices[it.key] = new_val


                else:
                    if(not lower_is_core and not higher_is_core
                       and  va==vb and da!=db ):
                        
                        lower_d, higher_d = (a, b) if da < db else (b, a)
                        lower_price = prices[lower_d.key]
                        higher_price = prices[higher_d.key]

                        if lower_price <= higher_price:
                            group: List[PriceElement] = []
                            for it in items:
                                if (
                                    it.product == a.product
                                    and it.product not in core_product
                                    and it.variant == a.variant
                                ):
                                    group.append(it)

                           #find max priority and price
                            base = None
                            for it in group:
                                if get_deductible_rank(it.deductible) == 1:
                                    p = prices[it.key]
                                    base = p if base is None else max(base, p)

                          
                            # -10% for every step
                            for it in group:
                                r = get_deductible_rank(it.deductible)  # 1,2,3
                                new_price = int(round(base * (0.9 ** (r - 1))))
                                if new_price != prices[it.key]:
                                    prices[it.key] = new_price
                                    changed = True
                    
                        
                    else:
                        if (not lower_is_core and not higher_is_core
                            and da==db and va!=vb):
                            lower_v, higher_v = (a, b) if va < vb else (b, a)
                            lower_price = prices[lower_v.key]
                            higher_price = prices[higher_v.key]

                            if ( lower_price >= higher_price ) :
                                group: List[PriceElement] = []
                                for it in items:
                                    if (
                                        it.product == a.product
                                        and it.product not in core_product
                                        and it.deductible == a.deductible
                                    ):
                                        group.append(it)

                                base = None
                                for it in group:
                                    if get_variant_rank(it.variant) == 1:
                                        p = prices[it.key]
                                        base = p if base is None else max(base, p)

                                if base is not None:
                                    for it in group:
                                        r = get_variant_rank(it.variant)  # 1,2,3
                                        new_price = int(round(base * (1.07 ** (r - 1))))
                                        if new_price != prices[it.key]:
                                            prices[it.key] = new_price
                                            changed = True


        if not changed:
            break


def run_example() -> None:
    example_prices_to_correct = {
    "mtpl": 400,  # core ok

    "limited_casco_compact_100": 820,
    "limited_casco_compact_200": 760,
    "limited_casco_compact_500": 650,

    "limited_casco_basic_100": 900,
    "limited_casco_basic_200": 780,
    "limited_casco_basic_500": 600,

    "limited_casco_comfort_100": 850,  # namerno: comfort_100 jeftiniji od basic_100 (variant greška)
    "limited_casco_comfort_200": 870,
    "limited_casco_comfort_500": 720,

    "limited_casco_premium_100": 880,  # namerno: premium_100 jeftiniji od comfort_100 (variant greška)
    "limited_casco_premium_200": 980,
    "limited_casco_premium_500": 800,

    "casco_compact_100": 750,
    "casco_compact_200": 700,
    "casco_compact_500": 620,

    "casco_basic_100": 830,
    "casco_basic_200": 760,
    "casco_basic_500": 650,

    "casco_comfort_100": 900,
    "casco_comfort_200": 820,
    "casco_comfort_500": 720,

    "casco_premium_100": 1050,
    "casco_premium_200": 950,
    "casco_premium_500": 1040,  # namerno: 500 skoro kao 100 (deductible greška jer 500 mora biti jeftiniji)
}


    items = build_price_items(example_prices_to_correct)

    print("=== BEFORE FIX ===")
    before_report = detect_inconsistencies(items, example_prices_to_correct)
    print(before_report if before_report.strip() else "(no inconsistencies found)")

    before_snapshot = dict(example_prices_to_correct)

    avg_prices = {
        "mtpl": 400.0,
        "limited_casco": 800.0,
        "casco": 900.0,
    }

    fix_products_inplace(items, example_prices_to_correct, avg_prices=avg_prices, max_iters=10)

    print("\n=== AFTER FIX (product-level only) ===")
    after_report = detect_inconsistencies(items, example_prices_to_correct)
    print(after_report if after_report.strip() else "(no inconsistencies found)")

    print("\n=== SAMPLE PRICES (before -> after) ===")
    sample_keys = [
        "mtpl",
        "limited_casco_compact_100",
        "limited_casco_premium_100",
        "casco_compact_100",
        "casco_premium_100",
    ]
    for k in sample_keys:
        print(f"{k}: {before_snapshot[k]} -> {example_prices_to_correct[k]}")

    print(example_prices_to_correct)


if __name__ == "__main__":
    run_example()
