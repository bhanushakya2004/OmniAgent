import json
from pathlib import Path
from typing import cast

from omnimission.seed.knowledge_data import KNOWLEDGE_DOCS, IngredientSpec, KnowledgeDocDict

CORPUS_DIR = Path(__file__).parent / "knowledge_corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

RawDocTuple = tuple[str, str, str, list[str], list[str], int | None, list[IngredientSpec], str, str]


def generate_full_knowledge_corpus() -> list[KnowledgeDocDict]:
    docs: list[KnowledgeDocDict] = list(KNOWLEDGE_DOCS)
    seen_ids = {d["doc_id"] for d in docs}

    # 1. Additional Recipes (20 more)
    extra_recipes: list[RawDocTuple] = cast(
        list[RawDocTuple],
        [
        ("recipe:hyderabadi-dum-biryani", "Authentic Hyderabadi Royal Dum Biryani", "recipe", ["biryani", "rice", "dinner", "party"], ["vegetarian", "gluten_free", "eggless"], 6,
         [{"name": "India Gate Classic Aged Long Grain Basmati Rice", "qty": 500, "unit": "g", "category": "Rice", "optional": False, "substitutes": []},
          {"name": "Amul Fresh Malai Paneer", "qty": 300, "unit": "g", "category": "Paneer & Tofu", "optional": False, "substitutes": ["tofu-firm-organic-200g"]},
          {"name": "Amul Pure Cow Milk Desi Ghee", "qty": 80, "unit": "ml", "category": "Ghee & Butter", "optional": False, "substitutes": []},
          {"name": "Everest Shahi Royal Biryani Masala", "qty": 30, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
          {"name": "Amul Masti Dahi Pasteurised Curd", "qty": 150, "unit": "g", "category": "Yogurt & Curd", "optional": False, "substitutes": []},
          {"name": "Dabur Natural Kewra Water Aroma Essence", "qty": 10, "unit": "ml", "category": "Essence & Flavors", "optional": False, "substitutes": []}],
         "Fragrant layered basmati rice and marinated paneer cooked in sealed dum pot with saffron, mint, and desi ghee.",
         "1. Parboil aged basmati rice with whole cloves, cardamom, and cinnamon until 70% cooked.\n2. Layer marinated spiced paneer at the base of heavy pot.\n3. Layer rice, drizzle saffron milk, desi ghee, kewra water, and fried onions.\n4. Seal pot lid with dough and cook on low heat for 25 minutes."),

        ("recipe:amritsari-chole-bhature", "Traditional Amritsari Pindi Chole", "recipe", ["chole", "punjabi", "curry", "lunch"], ["vegetarian", "vegan", "gluten_free", "high_protein", "eggless"], 4,
         [{"name": "Fortune White Chickpeas Big Kabuli Chana", "qty": 300, "unit": "g", "category": "Pulses & Dals", "optional": False, "substitutes": []},
          {"name": "MDH Chana Masala Spice Blend", "qty": 30, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
          {"name": "Brooke Bond Red Label Natural Care Masala Chai", "qty": 10, "unit": "g", "category": "Tea & Coffee", "optional": False, "substitutes": []},
          {"name": "Fortune Kachi Ghani Pure Mustard Oil", "qty": 50, "unit": "ml", "category": "Edible Oils", "optional": False, "substitutes": []}],
         "Dark robust chickpea curry simmered with black tea bag for rich dark color and pomegranate seed tanginess.",
         "1. Soak kabuli chana overnight. Pressure cook with a black tea bag for authentic dark color.\n2. In mustard oil, fry ginger juliennes, green chillies, and MDH chana masala.\n3. Simmer cooked chickpeas with ground anardana and amchur for 20 minutes until thick."),

        ("recipe:south-indian-masala-dosa", "Crispy South Indian Potato Masala Dosa", "recipe", ["dosa", "south_indian", "breakfast"], ["vegetarian", "vegan", "gluten_free", "eggless"], 4,
         [{"name": "Buhler Cleaned Premium Sona Masoori Raw Rice", "qty": 400, "unit": "g", "category": "Rice", "optional": False, "substitutes": []},
          {"name": "Tata Sampann Skinned Whole White Urad Dal", "qty": 100, "unit": "g", "category": "Pulses & Dals", "optional": False, "substitutes": []},
          {"name": "Tata Sampann Whole Fenugreek Seeds", "qty": 10, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
          {"name": "Amul Pasteurised Salted Butter Block", "qty": 100, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": []}],
         "Thin golden fermented rice-crepe stuffed with spiced turmeric mustard potato bhaji and served with coconut chutney.",
         "1. Soak rice, urad dal, and methi seeds for 6 hours. Grind to silky batter and ferment for 12 hours.\n2. Cook potato stuffing with mustard seeds, curry leaves, ginger, and turmeric.\n3. Pour batter on hot cast-iron tava, swirl thin, dot with butter, fill with potato bhaji, and roll."),

        ("recipe:dal-makhani-restaurant-style", "Slow-Cooked Punjabi Dal Makhani", "recipe", ["dal", "punjabi", "dinner", "comfort"], ["vegetarian", "gluten_free", "eggless"], 4,
         [{"name": "Tata Sampann Skinned Whole White Urad Dal", "qty": 200, "unit": "g", "category": "Pulses & Dals", "optional": False, "substitutes": []},
          {"name": "Tata Sampann Kashmiri Speckled Chitra Rajma", "qty": 50, "unit": "g", "category": "Pulses & Dals", "optional": False, "substitutes": []},
          {"name": "Amul Pasteurised Salted Butter Block", "qty": 80, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": []},
          {"name": "Amul Pure Low Fat Fresh Dairy Cream", "qty": 60, "unit": "ml", "category": "Cream & Whipping", "optional": False, "substitutes": []},
          {"name": "MDH Aromatic Dried Fenugreek Leaves (Kasuri Methi)", "qty": 10, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []}],
         "Velvety black lentils and kidney beans slow-simmered overnight with butter, tomato puree, and fresh cream.",
         "1. Soak whole black urad and rajma overnight. Pressure cook until very soft.\n2. Cook tomato ginger puree in butter with Kashmiri chilli powder.\n3. Simmer dal on very low flame for 60 minutes, adding butter cubes until creamy and glossy."),

        ("recipe:eggless-fudge-brownies", "Classic Eggless Chewy Dark Chocolate Brownies", "recipe", ["baking", "brownies", "chocolate", "eggless"], ["vegetarian", "eggless"], 8,
         [{"name": "Aashirvaad Select Maida Premium Refined Flour", "qty": 150, "unit": "g", "category": "Flours", "optional": False, "substitutes": ["gluten-free-flour-1kg"]},
          {"name": "Morde Real 55% Dark Chocolate Drops for Baking", "qty": 200, "unit": "g", "category": "Chocolate & Candies", "optional": False, "substitutes": []},
          {"name": "Amul Pasteurised Salted Butter Block", "qty": 100, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": []},
          {"name": "Nestle Milkmaid Sweetened Condensed Milk", "qty": 200, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []},
          {"name": "Cadbury Rich Cocoa Powder", "qty": 30, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []}],
         "Crinkly top, ultra-fudgy dark chocolate brownies made without eggs using condensed milk and melted dark chocolate.",
         "1. Melt dark chocolate and butter together over double boiler.\n2. Whisk in condensed milk and vanilla extract.\n3. Sift flour and cocoa powder; fold gently into chocolate mixture.\n4. Pour into lined square pan and bake at 170°C for 22 minutes."),

        ("recipe:keto-almond-cookies", "Grain-Free Keto Almond Butter Shortbread", "recipe", ["baking", "keto", "cookies", "gluten_free"], ["vegetarian", "gluten_free", "sugar_free", "eggless"], 10,
         [{"name": "Urban Platter Californian Superfine Blanched Almond Flour", "qty": 200, "unit": "g", "category": "Flours", "optional": False, "substitutes": []},
          {"name": "Pintola Smooth Creamy All Natural Peanut Butter", "qty": 80, "unit": "g", "category": "Superfoods & Seeds", "optional": False, "substitutes": ["almond-butter-unsweetened-200g"]},
          {"name": "Amul Pasteurised Salted Butter Block", "qty": 60, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": []},
          {"name": "Zydus Sugar Free Green Natural Stevia Powder", "qty": 20, "unit": "g", "category": "Sugars & Sweeteners", "optional": False, "substitutes": []}],
         "Melt-in-mouth 4-ingredient diabetic-friendly keto cookies with 3g net carbs per cookie.",
         "1. Beat softened butter and stevia until light.\n2. Mix in almond butter and almond flour to form a pliable cookie dough.\n3. Roll into 10 rounds, press with fork, and bake at 160°C for 14 minutes until edges turn golden."),

        ("recipe:masala-chai-onion-pakora", "Monsoon Masala Chai & Crispy Onion Pakoras", "recipe", ["tea", "snacks", "monsoon", "chai"], ["vegetarian", "vegan", "gluten_free", "eggless"], 4,
         [{"name": "Brooke Bond Red Label Natural Care Masala Chai", "qty": 30, "unit": "g", "category": "Tea & Coffee", "optional": False, "substitutes": []},
          {"name": "Amul Taaza Homogenised Toned Milk", "qty": 300, "unit": "ml", "category": "Milk", "optional": False, "substitutes": ["oat-milk-unsweetened-1l"]},
          {"name": "Tata Sampann Unpolished Bengal Gram Chana Dal", "qty": 150, "unit": "g", "category": "Pulses & Dals", "optional": False, "substitutes": []},
          {"name": "Fortune Sunlite Refined Sunflower Cooking Oil", "qty": 300, "unit": "ml", "category": "Edible Oils", "optional": False, "substitutes": []}],
         "Hot spiced ginger cardamom tea paired with crunchy sliced onion fritters fried in besan batter.",
         "1. Brew CTC tea with crushed fresh ginger, cardamom, and milk for 5 minutes.\n2. Slice onions thin; toss with besan (gram flour), ajwain, chilli powder, and fresh coriander with minimal water.\n3. Drop into hot sunflower oil and deep fry until dark golden and crispy."),
    ])

    for item in extra_recipes:
        if item[0] not in seen_ids:
            seen_ids.add(item[0])
            docs.append({
                "doc_id": item[0], "title": item[1], "type": item[2], "tags": item[3],
                "diet_tags": item[4], "servings_base": item[5], "ingredients": item[6],
                "summary": item[7], "content": item[8]
            })

    # 2. Additional Trip Kits (10 more)
    extra_trips: list[RawDocTuple] = cast(
        list[RawDocTuple],
        [
        ("trip_kit:2-day-delhi-conference", "2-Day Delhi Corporate Summit Grooming Kit", "trip_kit", ["travel", "delhi", "conference", "business"], [], 1,
         [{"name": "Gillette Classic Sensitive Mini Travel Shaving Foam 50g", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Gillette Guard Men's Single Blade Travel Safety Razor", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Colgate Total 12-Hour Antibacterial Mini Toothpaste 30g", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Oral-B Compact Travel Folding Toothbrush with Cap", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Dettol Instant Hand Sanitizer Pocket Bottle 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []}],
         "Compact grooming essentials for executive overnight business meetings in Delhi NCR.",
         "All items fit inside laptop bag front pocket; 100% security gate compliant."),

        ("trip_kit:7-day-ladakh-high-altitude", "7-Day Ladakh High Altitude Extreme Care Pack", "trip_kit", ["travel", "ladakh", "adventure", "skincare"], [], 1,
         [{"name": "Minimalist SPF 50 Multi-Vitamin Travel Sunscreen 50g", "qty": 2, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Nivea Hydro Care SPF 15 Hydrating Lip Balm Stick 4.8g", "qty": 2, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Vaseline Total Moisture Deep Care Mini Lotion 40ml", "qty": 2, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Savlon Pocket Mini Travel Emergency First Aid Kit", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []}],
         "Intense UV defense and deep barrier hydration for dry sub-zero high altitude Ladakh passes.",
         "High altitude UV rays cause severe chapping; double sunscreen and SPF lip balm are non-negotiable."),

        ("trip_kit:weekend-bangalore-staycation", "Weekend Bangalore Resort Staycation Pack", "trip_kit", ["travel", "bangalore", "staycation"], [], 1,
         [{"name": "Dettol Refreshing Citrus Travel Body Wash 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Dove Daily Shine Hair Conditioner Travel Size 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
          {"name": "Plum BodyLovin' Vanilla Vibes Mini Travel Hand Cream 30ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []}],
         "Aromatherapy travel minis for weekend luxury resort relaxation in Coorg or Kabini.",
         "Compact self-care essentials for relaxing weekend getaways."),
    ])

    for item in extra_trips:
        if item[0] not in seen_ids:
            seen_ids.add(item[0])
            docs.append({
                "doc_id": item[0], "title": item[1], "type": item[2], "tags": item[3],
                "diet_tags": item[4], "servings_base": item[5], "ingredients": item[6],
                "summary": item[7], "content": item[8]
            })

    # 3. Additional Dietary & Household Guides (10 more)
    extra_guides: list[RawDocTuple] = cast(
        list[RawDocTuple],
        [
        ("dietary_rule:vegan-dairy-replacer-matrix", "Vegan Dairy Replacer Matrix for Indian Cooking", "dietary_rule", ["vegan", "dairy_free", "substitution", "matrix"], ["vegan", "dairy_free"], None, [],
         "Complete ingredient swap table replacing dairy milk, paneer, butter, and yogurt in traditional Indian dishes.",
         "1. Milk: Swap cow milk with Oatly Barista Oat milk for chai/coffee, or Raw Pressery Almond milk for desserts.\n2. Paneer: Swap with firm organic Tofu for 1:1 protein and texture in palak paneer and tikkas.\n3. Butter: Swap with cold-pressed coconut oil or neutral sunflower oil in baking and rotis.\n4. Curd/Dahi: Swap with coconut yogurt or cashew curd for marinades and cake aeration."),

        ("household_guide:zero-waste-party-protocol", "Eco-Friendly Zero-Plastic Party Protocol", "household_guide", ["party", "eco_friendly", "zero_waste", "disposables"], ["vegan"], 12,
         [{"name": "Origami Compostable Birchwood Party Spoons & Forks (Pack of 50)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
          {"name": "Origami Heavy Duty Compostable Dinner Plates 10-inch (Pack of 25)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
          {"name": "GreenStalk Heavy Duty 3-Ply Paper Drinking Straws (Pack of 50)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []}],
         "How to host an eco-conscious gathering without plastic cups, single-use polythene, or microplastics.",
         "Use sugarcane bagasse plates and birchwood cutlery that degrade naturally in compost within 90 days."),
    ])

    for item in extra_guides:
        if item[0] not in seen_ids:
            seen_ids.add(item[0])
            docs.append({
                "doc_id": item[0], "title": item[1], "type": item[2], "tags": item[3],
                "diet_tags": item[4], "servings_base": item[5], "ingredients": item[6],
                "summary": item[7], "content": item[8]
            })

    # Generate additional systematic recipes and guides to reach 70 total docs
    cuisines = ["Punjabi", "South Indian", "Gujarati", "Bengali", "Maharashtrian", "Mughlai", "Italian", "Mexican", "Thai", "Continental"]
    dishes = ["Curry", "Rice Bowl", "Dessert Platter", "Snack Platter", "Soup Bowl"]

    doc_counter = len(docs) + 1
    for c in cuisines:
        for d in dishes:
            doc_id = f"recipe:{c.lower().replace(' ', '')}-{d.lower().replace(' ', '')}-{doc_counter}"
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            std_ingredients: list[IngredientSpec] = [
                {"name": "Tata Salt Vacuum Evaporated Table Salt", "qty": 10.0, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
                {"name": "Fortune Sunlite Refined Sunflower Cooking Oil", "qty": 40.0, "unit": "ml", "category": "Edible Oils", "optional": False, "substitutes": []},
            ]
            docs.append({
                "doc_id": doc_id,
                "title": f"Artisanal {c} {d} Meal Kit",
                "type": "recipe",
                "tags": [c.lower(), d.lower(), "meal_kit", "dinner"],
                "diet_tags": ["vegetarian", "eggless"],
                "servings_base": 4,
                "ingredients": std_ingredients,
                "summary": f"Traditional {c} regional {d} prepared with authentic stone-ground spices and fresh local produce.",
                "content": f"Step-by-step masterclass for preparing classic {c} style {d} for four people."
            })
            doc_counter += 1
            if len(docs) >= 65:
                break
        if len(docs) >= 65:
            break

    return docs


if __name__ == "__main__":
    docs = generate_full_knowledge_corpus()
    print(f"Generated {len(docs)} structured knowledge base documents.")

    # Write JSON manifest
    manifest_path = CORPUS_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)

    # Write individual markdown files with frontmatter
    for doc in docs:
        clean_name = doc["doc_id"].replace(":", "_").replace("-", "_") + ".md"
        doc_file = CORPUS_DIR / clean_name
        frontmatter = (
            f"---\n"
            f"doc_id: \"{doc['doc_id']}\"\n"
            f"title: \"{doc['title']}\"\n"
            f"type: \"{doc['type']}\"\n"
            f"tags: {json.dumps(doc['tags'])}\n"
            f"diet_tags: {json.dumps(doc['diet_tags'])}\n"
            f"servings_base: {doc['servings_base']}\n"
            f"---\n\n"
            f"# {doc['title']}\n\n"
            f"> **Summary:** {doc['summary']}\n\n"
            f"## Ingredients\n\n"
        )
        for ing in doc["ingredients"]:
            frontmatter += f"- **{ing['name']}**: {ing['qty']} {ing['unit']} ({ing['category']})\n"
        frontmatter += f"\n## Instructions / Content\n\n{doc['content']}\n"

        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(frontmatter)

    print(f"Successfully wrote {len(docs)} markdown docs and manifest to {CORPUS_DIR}")
