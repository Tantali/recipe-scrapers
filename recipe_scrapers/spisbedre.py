import json

from ._abstract import AbstractScraper
from ._grouping_utils import IngredientGroup


class SpisBedre(AbstractScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipe_json = json.loads(
            self.soup.find("div", id="app").attrs["data-page"]
        )["props"]["recipe"]

    @classmethod
    def host(cls):
        return "spisbedre.dk"

    def author(self):
        return self.schema.author()

    def title(self):
        return self.schema.title()

    def category(self):
        return ", ".join([type["name"] for type in self.recipe_json.get("tags", [])])

    def total_time(self):
        return self.schema.total_time()

    def yields(self):
        return self.schema.yields()

    def ingredients(self):
        result = []
        for ingredient_group in self.ingredient_groups():
            result.extend(ingredient_group.ingredients)
        return result

    def ingredient_groups(self):
        result = []
        servings = self.recipe_json.get("serving_size", 1)

        def format_ingredient(servings, ingredient):
            ingredient_elements = []

            def ingredient_label(amount, inflection, ingredient, prefix, suffix):
                label = []
                if ingredient is None:
                    return None

                if prefix:
                    label.append(prefix)

                if inflection in ["singular", "plural"]:
                    label.append(ingredient.get("name_" + inflection))
                elif amount and amount > 0 and amount < 2:
                    label.append(ingredient.get("name_singular"))
                else:
                    label.append(ingredient.get("name_plural"))

                if suffix:
                    label.append(suffix)

                return " ".join(label)

            def unit_label(amount, inflection, texts):
                label = []
                if amount is None or texts is None:
                    return None

                if texts.get("abbreviation"):
                    label.append(texts.get("abbreviation"))
                elif inflection in ["singular", "plural"]:
                    label.append(texts.get("name_" + inflection))
                elif amount > 0 and amount < 2:
                    label.append(texts.get("name_singular"))
                else:
                    label.append(texts.get("name_plural"))

                return " ".join(label)

            total_amount = amount = ingredient.get("amount")
            if amount:
                total_amount = amount * servings
                if int(total_amount) == total_amount:
                    total_amount = int(total_amount)
                ingredient_elements.append(str(total_amount))

            # For some reason unit_id 21 isn't rendered on the site, so we filter it as well
            if ingredient.get("unit_id") != 21:
                unit = unit_label(
                    total_amount,
                    ingredient.get("unit_inflection"),
                    ingredient.get("unit"),
                )
                if unit:
                    ingredient_elements.append(unit)

            label = ingredient_label(
                total_amount,
                ingredient.get("ingredient_inflection"),
                ingredient.get("ingredient"),
                ingredient.get("prefix"),
                ingredient.get("suffix"),
            )
            if label:
                ingredient_elements.append(label)

            return " ".join(ingredient_elements)

        for group in self.recipe_json.get("grouped_ingredients", []):
            current_group = {"ingredients": [], "purpose": group.get("title")}
            for ingredient in group.get("ingredients", []):
                formatted_ingredient = format_ingredient(servings, ingredient)
                if formatted_ingredient:
                    current_group["ingredients"].append(formatted_ingredient)

            result.append(current_group)

        return [
            IngredientGroup(
                ingredient_group["ingredients"], ingredient_group["purpose"]
            )
            for ingredient_group in result
        ]

    def instructions(self):
        result = []
        for group in self.recipe_json.get("grouped_instructions", []):
            for instruction in group.get("instructions", []):
                if instruction.get("instruction"):
                    result.append(instruction.get("instruction"))

        return "\n".join(result)

    def ratings(self):
        return self.schema.ratings()

    def cuisine(self):
        return self.schema.cuisine()

    def description(self):
        return self.schema.description()
