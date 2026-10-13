"""Authored knowledge base corpus for Recipe-RAG, travel kits, dietary guidelines, and party planning."""

from typing import TypedDict


class IngredientSpec(TypedDict, total=False):
    name: str
    qty: float
    unit: str
    category: str
    optional: bool
    substitutes: list[str]


class KnowledgeDocDict(TypedDict):
    doc_id: str
    title: str
    type: str  # recipe, trip_kit, dietary_rule, household_guide
    tags: list[str]
    diet_tags: list[str]
    servings_base: int | None
    ingredients: list[IngredientSpec]
    summary: str
    content: str


KNOWLEDGE_DOCS: list[KnowledgeDocDict] = [
    # ==========================================
    # 1. HEADLINE RECIPE: Eggless Strawberry Cake
    # ==========================================
    {
        "doc_id": "recipe:eggless-strawberry-cake",
        "title": "Fresh Eggless Strawberry Cream Cake",
        "type": "recipe",
        "tags": ["baking", "cake", "strawberry", "eggless", "dessert", "party"],
        "diet_tags": ["vegetarian", "eggless"],
        "servings_base": 8,
        "summary": "Soft moist vanilla sponge layered with Mahabaleshwar strawberry crush, whipped non-dairy cream, and fresh strawberry slices.",
        "ingredients": [
            {"name": "Maida Premium Refined Flour", "qty": 250, "unit": "g", "category": "Flours", "optional": False, "substitutes": ["cake-flour-fine-1kg", "gluten-free-flour-1kg"]},
            {"name": "Superfine Powdered Sugar", "qty": 180, "unit": "g", "category": "Sugars & Sweeteners", "optional": False, "substitutes": ["caster-sugar-1kg"]},
            {"name": "Double Action Baking Powder", "qty": 10, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []},
            {"name": "Pure Edible Baking Soda", "qty": 5, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []},
            {"name": "Amul Masti Dahi Curd", "qty": 200, "unit": "g", "category": "Yogurt & Curd", "optional": False, "substitutes": ["greek-yogurt-400g", "condensed-milk-400g"]},
            {"name": "Fortune Sunlite Refined Sunflower Cooking Oil", "qty": 80, "unit": "ml", "category": "Edible Oils", "optional": False, "substitutes": ["amul-butter-500g"]},
            {"name": "Sprig Natural Bourbon Vanilla Extract", "qty": 5, "unit": "ml", "category": "Essence & Flavors", "optional": False, "substitutes": []},
            {"name": "Fresh Mahabaleshwar Sweet Strawberries", "qty": 200, "unit": "g", "category": "Fresh Fruits", "optional": False, "substitutes": ["strawberry-compote-250g"]},
            {"name": "Mapro Whole Fruit Strawberry Crush", "qty": 100, "unit": "ml", "category": "Fruit Crushes & Syrups", "optional": False, "substitutes": ["strawberry-compote-250g"]},
            {"name": "Rich's Non-Dairy Whip Topping Cream", "qty": 300, "unit": "ml", "category": "Cream & Whipping", "optional": False, "substitutes": ["amul-fresh-cream-250ml"]},
            {"name": "Oddy Ecobake Non-Stick Baking Parchment Paper", "qty": 1, "unit": "piece", "category": "Kitchen Disposables", "optional": True, "substitutes": []},
            {"name": "HomeBasics Anodized Aluminium Round Cake Pan 8-inch", "qty": 1, "unit": "piece", "category": "Bakeware", "optional": True, "substitutes": []},
        ],
        "content": (
            "An authentic bakery-style layered strawberry gateau prepared without eggs.\n"
            "1. Sponge Aeration: Whisk curd and powdered sugar until smooth, then add baking powder and baking soda. Let rest for 5 minutes until frothy bubbles form.\n"
            "2. Wet & Dry Fold: Gently fold in oil, vanilla extract, and sifted maida flour without over-beating.\n"
            "3. Bake: Pour into parchment-lined 8-inch cake tin and bake at 180°C for 30-35 minutes until a toothpick comes out clean.\n"
            "4. Assembly: Slice cooled sponge into 2 layers. Soak each layer with water-diluted strawberry crush. Pipe chilled whipped cream, lay fresh strawberry slices, and frost the exterior."
        ),
    },

    # ==========================================
    # 2. RECIPE: High-Protein Eggless Chocolate Cake
    # ==========================================
    {
        "doc_id": "recipe:high-protein-eggless-chocolate-cake",
        "title": "High-Protein Eggless Dark Chocolate Fudge Cake",
        "type": "recipe",
        "tags": ["baking", "cake", "chocolate", "high_protein", "eggless", "fitness"],
        "diet_tags": ["vegetarian", "eggless", "high_protein"],
        "servings_base": 6,
        "summary": "Rich decadent chocolate cake fortified with whey or plant protein powder, dark cocoa, and Greek yogurt moisture.",
        "ingredients": [
            {"name": "Urban Platter Californian Superfine Blanched Almond Flour", "qty": 150, "unit": "g", "category": "Flours", "optional": False, "substitutes": ["maida-flour-1kg"]},
            {"name": "Cadbury Rich Cocoa Powder", "qty": 50, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": ["dutch-processed-black-cocoa-100g"]},
            {"name": "MuscleBlaze Raw Whey Protein Concentrate 80%", "qty": 60, "unit": "g", "category": "Protein Supplements", "optional": False, "substitutes": ["plant-protein-chocolate-500g"]},
            {"name": "Double Action Baking Powder", "qty": 8, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []},
            {"name": "Epigamia Natural Greek Yogurt High Protein Plain Curd", "qty": 200, "unit": "g", "category": "Yogurt & Curd", "optional": False, "substitutes": ["curd-dahi-amul-400g"]},
            {"name": "Nestle Milkmaid Sweetened Condensed Milk", "qty": 150, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": ["caster-sugar-1kg"]},
            {"name": "Morde Real 55% Dark Chocolate Drops for Baking", "qty": 100, "unit": "g", "category": "Chocolate & Candies", "optional": False, "substitutes": ["white-chocolate-chips-200g"]},
            {"name": "Sprig Natural Bourbon Vanilla Extract", "qty": 5, "unit": "ml", "category": "Essence & Flavors", "optional": False, "substitutes": []},
        ],
        "content": (
            "A fitness-friendly protein dessert delivering 16g protein per slice.\n"
            "1. Sift almond flour, cocoa powder, whey protein powder, and baking powder together.\n"
            "2. In a separate bowl, blend Greek yogurt, condensed milk, and vanilla extract.\n"
            "3. Fold wet and dry ingredients gently together with melted dark chocolate chips.\n"
            "4. Bake in preheated oven at 175°C for 25 minutes. Serve warm with greek yogurt or fresh berries."
        ),
    },

    # ==========================================
    # 3. RECIPE: Vegan Gluten-Free Blueberry Oat Muffins
    # ==========================================
    {
        "doc_id": "recipe:vegan-gluten-free-blueberry-muffins",
        "title": "Vegan Gluten-Free Blueberry Breakfast Muffins",
        "type": "recipe",
        "tags": ["baking", "muffins", "vegan", "gluten_free", "breakfast"],
        "diet_tags": ["vegetarian", "vegan", "dairy_free", "gluten_free", "eggless"],
        "servings_base": 6,
        "summary": "Hearty wholesome morning muffins loaded with wild blueberries, rolled oat flour, and flaxseed egg replacement.",
        "ingredients": [
            {"name": "True Elements Rolled Oat Flour Certified Gluten Free", "qty": 200, "unit": "g", "category": "Flours", "optional": False, "substitutes": ["gluten-free-flour-1kg"]},
            {"name": "True Elements Cold Milled Golden Flaxseed Powder", "qty": 20, "unit": "g", "category": "Superfoods", "optional": False, "substitutes": ["chia-seeds-organic-250g"]},
            {"name": "Oatly Barista Edition Gluten Free Oat Milk", "qty": 180, "unit": "ml", "category": "Plant Milk", "optional": False, "substitutes": ["almond-milk-unsweetened-1l"]},
            {"name": "Fortune Sunlite Refined Sunflower Cooking Oil", "qty": 60, "unit": "ml", "category": "Edible Oils", "optional": False, "substitutes": []},
            {"name": "Fresh Imported Premium Blueberries Punnet", "qty": 125, "unit": "g", "category": "Fresh Fruits", "optional": False, "substitutes": ["fresh-strawberries-200g"]},
            {"name": "Double Action Baking Powder", "qty": 8, "unit": "g", "category": "Baking Essentials", "optional": False, "substitutes": []},
            {"name": "Trust Classic Natural Demerara Brown Sugar", "qty": 80, "unit": "g", "category": "Sugars & Sweeteners", "optional": False, "substitutes": ["caster-sugar-1kg"]},
        ],
        "content": (
            "Golden vegan morning muffins with bursting pockets of warm blueberries.\n"
            "1. Make Flax Egg: Combine 2 tablespoons flaxseed powder with 6 tablespoons warm oat milk. Let sit 10 minutes to thicken.\n"
            "2. Combine dry gluten-free oat flour, brown sugar, and baking powder.\n"
            "3. Mix flax egg, sunflower oil, and remaining oat milk. Fold together gently.\n"
            "4. Fold in fresh blueberries and spoon into muffin tin. Bake at 190°C for 22 minutes."
        ),
    },

    # ==========================================
    # 4. RECIPE: Mumbai Street-Style Butter Pav Bhaji
    # ==========================================
    {
        "doc_id": "recipe:mumbai-butter-pav-bhaji",
        "title": "Authentic Mumbai Street Butter Pav Bhaji",
        "type": "recipe",
        "tags": ["cooking", "street_food", "dinner", "party", "mumbai"],
        "diet_tags": ["vegetarian", "eggless"],
        "servings_base": 6,
        "summary": "Classic Mumbai street food spiced vegetable mash served with toasted butter pav and lemon wedges.",
        "ingredients": [
            {"name": "Everest Pav Bhaji Masala", "qty": 30, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
            {"name": "Amul Pasteurised Salted Butter Block", "qty": 150, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": ["pure-ghee-amul-1l"]},
            {"name": "Dabur Hommade Ginger Garlic Paste", "qty": 40, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": ["fresh-ginger-250g", "fresh-garlic-peeled-200g"]},
            {"name": "Everest Kashmiri Lal Stemless Mild Red Chilli Powder", "qty": 15, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
            {"name": "Tata Salt Vacuum Evaporated Iodised Table Salt", "qty": 10, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
            {"name": "Fresh Farm Yellow Seedless Juicy Lemons", "qty": 3, "unit": "piece", "category": "Fresh Fruits", "optional": False, "substitutes": []},
            {"name": "Fresh Hydroponic Cleaned Coriander Leaves", "qty": 50, "unit": "g", "category": "Fresh Fruits", "optional": False, "substitutes": []},
        ],
        "content": (
            "Spicy, buttery Mumbai street food classic.\n"
            "1. Boil potatoes, cauliflower, and green peas until tender. Mash thoroughly.\n"
            "2. Heat butter on a flat tava. Saute chopped onions, ginger garlic paste, and tomatoes until soft.\n"
            "3. Add Everest Pav Bhaji masala and Kashmiri red chilli powder. Mash together with butter.\n"
            "4. Add mashed vegetables with warm water and simmer for 15 minutes, mashing continuously.\n"
            "5. Serve with generous dollop of Amul butter, chopped onions, and fresh lemon juice."
        ),
    },

    # ==========================================
    # 5. RECIPE: Royal Shahi Paneer Butter Masala
    # ==========================================
    {
        "doc_id": "recipe:shahi-paneer-butter-masala",
        "title": "Restaurant-Style Shahi Paneer Butter Masala",
        "type": "recipe",
        "tags": ["cooking", "curry", "paneer", "dinner", "party"],
        "diet_tags": ["vegetarian", "gluten_free", "high_protein", "eggless"],
        "servings_base": 4,
        "summary": "Velvety cashew tomato gravy simmered with fresh malai paneer cubes, butter, and kasuri methi.",
        "ingredients": [
            {"name": "Amul Fresh Malai Paneer 200g Vacuum Pack", "qty": 400, "unit": "g", "category": "Paneer & Tofu", "optional": False, "substitutes": ["tofu-firm-organic-200g"]},
            {"name": "Amul Pasteurised Salted Butter Block", "qty": 50, "unit": "g", "category": "Butter & Margarine", "optional": False, "substitutes": ["pure-ghee-amul-1l"]},
            {"name": "Amul Pure Low Fat Fresh Dairy Cream", "qty": 100, "unit": "ml", "category": "Cream & Whipping", "optional": False, "substitutes": []},
            {"name": "Nutraj Mangalore Black Pepper Roasted Cashews", "qty": 50, "unit": "g", "category": "Dry Fruits & Nuts", "optional": False, "substitutes": []},
            {"name": "MDH Aromatic Dried Fenugreek Leaves (Kasuri Methi)", "qty": 10, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
            {"name": "Everest Kashmiri Lal Stemless Mild Red Chilli Powder", "qty": 15, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
            {"name": "Catch Superb 13-Spice Garam Masala Powder", "qty": 5, "unit": "g", "category": "Spices & Salt", "optional": False, "substitutes": []},
        ],
        "content": (
            "A rich Mughlai vegetarian delicacy.\n"
            "1. Gravy Base: Boil tomatoes, cashews, and whole spices for 15 minutes, then blend into a silky smooth puree.\n"
            "2. Tempering: Melt butter in pan, add Kashmiri chilli powder and the strained tomato-cashew puree.\n"
            "3. Simmer: Cook on low flame for 12 minutes until butter releases on edges.\n"
            "4. Finish: Add fresh malai paneer cubes, fresh dairy cream, crushed kasuri methi, and garam masala."
        ),
    },

    # ==========================================
    # 6. TRAVEL KIT: 3-Day Mumbai Monsoon Business Trip
    # ==========================================
    {
        "doc_id": "trip_kit:3-day-mumbai-business",
        "title": "3-Day Mumbai Business Trip Travel-Size Toiletries Kit",
        "type": "trip_kit",
        "tags": ["travel", "toiletries", "mumbai", "business", "airline_compliant"],
        "diet_tags": [],
        "servings_base": 1,
        "summary": "Airline hand-baggage compliant (all liquids <=100ml) compact personal grooming kit for a 72-hour metro trip.",
        "ingredients": [
            {"name": "Pantene Pro-V Hair Fall Control Mini Travel Shampoo 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Colgate Total 12-Hour Antibacterial Mini Toothpaste 30g", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Oral-B Compact Travel Folding Toothbrush with Cap", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Nivea Pearl & Beauty Pocket Deodorant Roll-on 35ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Dettol Instant Hand Sanitizer Pocket Bottle 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Minimalist SPF 50 Multi-Vitamin Travel Sunscreen 50g", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Himalaya Purifying Neem Mini Travel Face Wash 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Dettol Disinfectant Pocket Wet Wipes (Pack of 10)", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Listerine Cool Mint Antiseptic Travel Mouthwash 80ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": True, "substitutes": []},
        ],
        "content": (
            "Complete airport cabin-baggage compliant packing checklist.\n"
            "- All bottles are strictly 50ml or under (airline security rules require ≤ 100ml).\n"
            "- Includes folding toothbrush and antibacterial wipes for clean travel across airports, cabs, and hotels.\n"
            "- Total liquids volume fits inside a standard 1-quart transparent toiletry pouch."
        ),
    },

    # ==========================================
    # 7. TRAVEL KIT: 5-Day Goa Beach Holiday Kit
    # ==========================================
    {
        "doc_id": "trip_kit:5-day-goa-beach",
        "title": "5-Day Goa Beach Vacation Skincare & Hygiene Kit",
        "type": "trip_kit",
        "tags": ["travel", "beach", "goa", "sunscreen", "vacation"],
        "diet_tags": [],
        "servings_base": 1,
        "summary": "Sun protection, soothing aloe, insect defense, and compact travel hygiene for coastal beach travel.",
        "ingredients": [
            {"name": "Minimalist SPF 50 Multi-Vitamin Travel Sunscreen 50g", "qty": 2, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Dettol Refreshing Citrus Travel Body Wash 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Dove Daily Shine Hair Conditioner Travel Size 50ml", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Nivea Hydro Care SPF 15 Hydrating Lip Balm Stick 4.8g", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Savlon Pocket Mini Travel Emergency First Aid Kit", "qty": 1, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
            {"name": "Dettol Disinfectant Pocket Wet Wipes (Pack of 10)", "qty": 2, "unit": "piece", "category": "Travel Essentials", "optional": False, "substitutes": []},
        ],
        "content": (
            "Essential coastal travel hygiene kit.\n"
            "- High SPF water-resistant broad spectrum sunscreen to prevent sunburn during beach outings.\n"
            "- Travel conditioner to protect hair from salt water dryness.\n"
            "- Pocket first aid kit for scrapes, shells, or bike tours."
        ),
    },

    # ==========================================
    # 8. PARTY GUIDE: 8-Guest House Party Snacks & Disposables
    # ==========================================
    {
        "doc_id": "party_guide:8-guest-house-party",
        "title": "House Party Kit for 8 Guests (Snacks, Drinks & Tableware)",
        "type": "household_guide",
        "tags": ["party", "snacks", "drinks", "disposables", "host"],
        "diet_tags": ["vegetarian", "eggless"],
        "servings_base": 8,
        "summary": "Zero-stress hosting checklist calculating exact drink cans, snack portions, compostable cups, and cleaning bags for 8 people.",
        "ingredients": [
            {"name": "Origami Biodegradable Paper Beverage Cups (Pack of 50)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
            {"name": "Origami Heavy Duty Compostable Dinner Plates 10-inch (Pack of 25)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
            {"name": "Paseo Luxury 2-Ply Party Table Napkins (Pack of 100)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
            {"name": "Origami Compostable Birchwood Party Spoons & Forks (Pack of 50)", "qty": 1, "unit": "piece", "category": "Disposables", "optional": False, "substitutes": []},
            {"name": "Schweppes Spiced Ginger Ale Can 300ml (Pack of 6)", "qty": 2, "unit": "piece", "category": "Soft Drinks & Mixers", "optional": False, "substitutes": ["coca-cola-can-300ml-6pack", "tonic-water-schweppes-300ml-6can"]},
            {"name": "Coca-Cola Original Refreshing Taste Can 300ml (Pack of 6)", "qty": 2, "unit": "piece", "category": "Soft Drinks & Mixers", "optional": False, "substitutes": ["thums-up-can-300ml-6pack"]},
            {"name": "Lay's Classic Salted Potato Chips Big Sharing Bag 115g", "qty": 3, "unit": "piece", "category": "Chips", "optional": False, "substitutes": ["nachos-corn-chips-cheese-150g"]},
            {"name": "Doritos Cheese Supreme Crunchy Tortilla Nachos 150g", "qty": 2, "unit": "piece", "category": "Chips", "optional": False, "substitutes": []},
            {"name": "Cantina Mexican Spicy Tomato Chunky Salsa Dip 250g", "qty": 1, "unit": "piece", "category": "Dips & Sauces", "optional": False, "substitutes": []},
            {"name": "Haldiram's Nagpur Aloo Bhujia Spicy Crunchy Snack 400g", "qty": 1, "unit": "piece", "category": "Namkeen", "optional": False, "substitutes": []},
            {"name": "Shalimar Premium Oxo-Biodegradable Dustbin Trash Bags Medium (Pack of 30)", "qty": 1, "unit": "piece", "category": "Cleaning Essentials", "optional": False, "substitutes": []},
        ],
        "content": (
            "Hosting formula for 8 people:\n"
            "- Beverage formula: 3-4 drinks per guest = ~24 cans (2x Ginger Ale 6-packs + 2x Cola 6-packs).\n"
            "- Snack formula: 100g chips/nachos per person = ~800g total (3x Lays + 2x Doritos + 1x Salsa dip).\n"
            "- Disposable buffer: 3 cups per guest = 24-30 cups (1 pack of 50 covers the full evening).\n"
            "- Post-party waste: Biodegradable trash bags make cleanup take under 5 minutes."
        ),
    },

    # ==========================================
    # 9. DIETARY RULE: Eggless Baking Mechanics & Replacements
    # ==========================================
    {
        "doc_id": "dietary_rule:eggless-baking-mechanics",
        "title": "Eggless Baking Substitution Rules & Ratios",
        "type": "dietary_rule",
        "tags": ["dietary", "eggless", "baking", "science", "substitution"],
        "diet_tags": ["vegetarian", "vegan", "eggless"],
        "servings_base": None,
        "ingredients": [],
        "summary": "Comprehensive scientific conversion ratios for replacing whole eggs in cake sponges, cookies, and brownies.",
        "content": (
            "When baking eggless, eggs provide three primary functions: Moisture, Leavening (lift), and Emulsification (binding).\n"
            "Use these exact substitutions per 1 large egg:\n"
            "1. Dahi/Curd or Greek Yogurt: 1/4 cup (60g) thick curd + 1/4 tsp baking soda. Excellent for soft fluffy vanilla and fruit sponges.\n"
            "2. Sweetened Condensed Milk: 1/4 cup (60g) condensed milk (reduce recipe sugar by 2 tablespoons). Provides rich caramel crumb and tender moisture.\n"
            "3. Flax Egg (Vegan): 1 tbsp (10g) ground golden flaxseed powder + 3 tbsp warm water. Whisk and rest for 10 minutes until gelatinous. Superb for chocolate cakes, brownies, and nutty breads.\n"
            "4. Vinegar & Baking Soda Reaction: 1 tbsp white vinegar or apple cider vinegar + 1 tsp baking soda. Chemical reaction releases carbon dioxide, producing tall airy sponge cakes without eggs.\n"
            "5. Mashed Banana: 1/4 cup ripe banana. Best for pancakes and tea loaves (adds slight banana flavor)."
        ),
    },

    # ==========================================
    # 10. DIETARY RULE: Celiac-Safe Gluten-Free Flours
    # ==========================================
    {
        "doc_id": "dietary_rule:gluten-free-flour-guide",
        "title": "Gluten-Free Flour Selection & Cross-Contamination Rules",
        "type": "dietary_rule",
        "tags": ["dietary", "gluten_free", "celiac", "flours"],
        "diet_tags": ["gluten_free", "vegan", "vegetarian"],
        "servings_base": None,
        "ingredients": [],
        "summary": "Rules for choosing gluten-free flours and binders (almond, oat, tapioca, rice) and avoiding wheat cross-contact.",
        "content": (
            "Gluten provides elasticity and traps gas in baked goods. To replace wheat flour safely:\n"
            "1. Almond Flour: 100% grain-free blanched ground almonds. High protein and healthy fats. Best for soft cakes, macarons, and keto baking.\n"
            "2. Certified Gluten-Free Oat Flour: Rich in soluble fiber, gives familiar bakery chewiness. Must be certified gluten-free to avoid cross-contamination in grain mills.\n"
            "3. Tapioca Starch / Corn Starch: Added in 15-20% ratio to gluten-free flour blends to mimic gluten's stretch and prevent crumbly texture.\n"
            "4. Xanthan Gum or Psyllium Husk: Add 1/2 tsp per cup of gluten-free flour to provide tensile strength."
        ),
    },
]
