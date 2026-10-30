
import database_neon

products = database_neon.search_products("610910")

print("PRODUCT SEARCH:")
for product in products:
    print(product)

print("\nCHINA TO TURKEY:")
print(
    database_neon.fetch_direction_series(
        "CN_TO_TR", "610910", 2019, 2025
    )
)

print("\nTURKEY TO CHINA:")
print(
    database_neon.fetch_direction_series(
        "TR_TO_CN", "610910", 2019, 2025
    )
)
