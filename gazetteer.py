# -*- coding: utf-8 -*-
"""
Gazetteer France (métropole + outre-mer) pour la carte Libération.

Chaque entrée : (nom_affiché, requête_geocodage, catégorie)
- nom_affiché : forme cherchée dans les tags / titres / chapôs
- requête_geocodage : chaîne envoyée à Nominatim (lève les ambiguïtés)
- catégorie : "region" | "departement" | "ville" | "territoire"

RISKY_IN_TEXT : noms trop ambigus pour être cherchés dans le texte libre
(titre/chapô) — ils ne sont acceptés QUE s'ils apparaissent dans les tags.
Exemple : "Tours" (tours de scrutin), "Nord" (le nord du pays), "Somme"…

Liste volontairement ajustable : ajoute/retire des entrées librement.
"""

REGIONS = [
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
    "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France",
    "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie",
    "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
]

TERRITOIRES_OUTREMER = [
    "Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte",
    "Nouvelle-Calédonie", "Polynésie française", "Wallis-et-Futuna",
    "Saint-Pierre-et-Miquelon", "Saint-Martin", "Saint-Barthélemy",
]

DEPARTEMENTS = [
    "Ain", "Aisne", "Allier", "Alpes-de-Haute-Provence", "Hautes-Alpes",
    "Alpes-Maritimes", "Ardèche", "Ardennes", "Ariège", "Aube", "Aude",
    "Aveyron", "Bouches-du-Rhône", "Calvados", "Cantal", "Charente",
    "Charente-Maritime", "Cher", "Corrèze", "Corse-du-Sud", "Haute-Corse",
    "Côte-d'Or", "Côtes-d'Armor", "Creuse", "Dordogne", "Doubs", "Drôme",
    "Eure", "Eure-et-Loir", "Finistère", "Gard", "Haute-Garonne", "Gers",
    "Gironde", "Hérault", "Ille-et-Vilaine", "Indre", "Indre-et-Loire",
    "Isère", "Jura", "Landes", "Loir-et-Cher", "Loire", "Haute-Loire",
    "Loire-Atlantique", "Loiret", "Lot", "Lot-et-Garonne", "Lozère",
    "Maine-et-Loire", "Manche", "Marne", "Haute-Marne", "Mayenne",
    "Meurthe-et-Moselle", "Meuse", "Morbihan", "Moselle", "Nièvre", "Nord",
    "Oise", "Orne", "Pas-de-Calais", "Puy-de-Dôme", "Pyrénées-Atlantiques",
    "Hautes-Pyrénées", "Pyrénées-Orientales", "Bas-Rhin", "Haut-Rhin",
    "Rhône", "Haute-Saône", "Saône-et-Loire", "Sarthe", "Savoie",
    "Haute-Savoie", "Seine-Maritime", "Seine-et-Marne", "Yvelines",
    "Deux-Sèvres", "Somme", "Tarn", "Tarn-et-Garonne", "Var", "Vaucluse",
    "Vendée", "Vienne", "Haute-Vienne", "Vosges", "Yonne",
    "Territoire de Belfort", "Essonne", "Hauts-de-Seine",
    "Seine-Saint-Denis", "Val-de-Marne", "Val-d'Oise",
]

# Villes : préfectures + grandes villes + villes régulièrement couvertes.
# Tuple (nom, requête geocodage) quand une précision est nécessaire.
VILLES = [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes",
    "Montpellier", "Strasbourg", "Bordeaux", "Lille", "Rennes", "Reims",
    "Toulon", "Saint-Étienne", "Le Havre", "Grenoble", "Dijon", "Angers",
    "Nîmes", "Clermont-Ferrand", "Le Mans", "Aix-en-Provence", "Brest",
    "Tours", "Amiens", "Limoges", "Annecy", "Perpignan", "Boulogne-Billancourt",
    "Metz", "Besançon", "Orléans", "Rouen", "Mulhouse", "Caen", "Nancy",
    "Saint-Denis", "Argenteuil", "Montreuil", "Roubaix", "Tourcoing",
    "Nanterre", "Avignon", "Vitry-sur-Seine", "Créteil", "Dunkerque",
    "Poitiers", "Aubervilliers", "Versailles", "Aulnay-sous-Bois",
    "Colombes", "Saint-Pierre", "La Rochelle", "Champigny-sur-Marne",
    "Antibes", "Cannes", "Calais", "Béziers", "Colmar", "Bourges",
    "Drancy", "Mérignac", "Saint-Nazaire", "Valence", "Ajaccio",
    "Issy-les-Moulineaux", "Villeneuve-d'Ascq", "Levallois-Perret",
    "Noisy-le-Grand", "Quimper", "La Seyne-sur-Mer", "Antony", "Troyes",
    "Neuilly-sur-Seine", "Sarcelles", "Les Abymes", "Vénissieux",
    "Clichy", "Lorient", "Pau", "Évry-Courcouronnes", "Ivry-sur-Seine",
    "Cergy", "Montauban", "Niort", "Chambéry", "Saint-Quentin",
    "Villejuif", "Hyères", "Beauvais", "Cholet", "Bobigny", "Vannes",
    "Fréjus", "La Roche-sur-Yon", "Charleville-Mézières", "Narbonne",
    "Bayonne", "Chartres", "Sète", "Arles", "Saint-Brieuc",
    "Angoulême", "Boulogne-sur-Mer", "Wattrelos", "Gap", "Compiègne",
    "Belfort", "Blois", "Châteauroux", "Chalon-sur-Saône", "Tarbes",
    "Bastia", "Corbeil-Essonnes", "Sevran", "Meaux", "Évreux",
    "Châlons-en-Champagne", "Brive-la-Gaillarde", "Albi", "Carcassonne",
    "Martigues", "Aubagne", "Saint-Malo", "Auxerre", "Cherbourg-en-Cotentin",
    "Mantes-la-Jolie", "Melun", "Laval", "Bourg-en-Bresse", "Roanne",
    "Agen", "Périgueux", "Mâcon", "Nevers", "Vichy", "Montluçon",
    "Épinal", "Auch", "Rodez", "Mende", "Cahors", "Guéret", "Tulle",
    "Aurillac", "Le Puy-en-Velay", "Privas", "Foix", "Digne-les-Bains",
    "Moulins", "Chaumont", "Bar-le-Duc", "Épernay", "Saint-Lô",
    "Alençon", "Vesoul", "Lons-le-Saunier", "Dole", "Montbéliard",
    "Thionville", "Forbach", "Sarreguemines", "Haguenau", "Sélestat",
    "Saint-Dié-des-Vosges", "Verdun", "Sedan", "Laon", "Soissons",
    "Abbeville", "Arras", "Lens", "Liévin", "Douai", "Valenciennes",
    "Maubeuge", "Cambrai", "Armentières", "Hazebrouck", "Berck",
    "Le Touquet-Paris-Plage", "Étaples", "Fécamp", "Dieppe", "Lisieux",
    "Bayeux", "Granville", "Avranches", "Fougères", "Vitré", "Redon",
    "Dinan", "Lannion", "Guingamp", "Morlaix", "Concarneau", "Douarnenez",
    "Pontivy", "Auray", "Ploërmel", "Ancenis", "Châteaubriant",
    "Saumur", "Segré-en-Anjou Bleu", "La Flèche", "Sablé-sur-Sarthe",
    "Mamers", "Vendôme", "Romorantin-Lanthenay", "Vierzon", "Issoudun",
    "Loches", "Chinon", "Pithiviers", "Montargis", "Gien", "Dreux",
    "Châteaudun", "Nogent-le-Rotrou", "Provins", "Fontainebleau",
    "Coulommiers", "Rambouillet", "Étampes", "Palaiseau", "Massy",
    "Roissy-en-France", "Saint-Ouen-sur-Seine", "Pantin", "Bagnolet",
    "Fontenay-sous-Bois", "Choisy-le-Roi", "Athis-Mons", "Trappes",
    "Poissy", "Saint-Germain-en-Laye", "Gennevilliers", "Asnières-sur-Seine",
    "Courbevoie", "Puteaux", "Rueil-Malmaison", "Suresnes", "Meudon",
    "Montrouge", "Bagneux", "Cachan", "Alfortville", "Maisons-Alfort",
    "Saint-Maur-des-Fossés", "Nogent-sur-Marne", "Rosny-sous-Bois",
    "Noisy-le-Sec", "Bondy", "Livry-Gargan", "Le Blanc-Mesnil",
    "Villepinte", "Tremblay-en-France", "Gonesse", "Garges-lès-Gonesse",
    "Villiers-le-Bel", "Ermont", "Franconville", "Pontoise", "Bezons",
    "Houilles", "Sartrouville", "Conflans-Sainte-Honorine",
    "Vigneux-sur-Seine", "Draveil", "Savigny-sur-Orge", "Viry-Châtillon",
    "Grigny", "Ris-Orangis", "Corbeil", "Brétigny-sur-Orge", "Arpajon",
    "Dourdan", "Longjumeau", "Chelles", "Torcy", "Lognes", "Pontault-Combault",
    "Roissy-en-Brie", "Ozoir-la-Ferrière", "Brie-Comte-Robert",
    "Villeurbanne", "Vaulx-en-Velin", "Bron", "Saint-Priest", "Givors",
    "Villefranche-sur-Saône", "Vienne", "Bourgoin-Jallieu", "Voiron",
    "Échirolles", "Fontaine", "Saint-Martin-d'Hères", "Montélimar",
    "Romans-sur-Isère", "Aubenas", "Annonay", "Saint-Chamond",
    "Firminy", "Rive-de-Gier", "Thonon-les-Bains", "Annemasse",
    "Cluses", "Sallanches", "Chamonix-Mont-Blanc", "Albertville",
    "Aix-les-Bains", "Oyonnax", "Ambérieu-en-Bugey", "Gex",
    "Thiers", "Issoire", "Riom", "Cournon-d'Auvergne", "Saint-Flour",
    "Millau", "Villefranche-de-Rouergue", "Decazeville", "Figeac",
    "Castres", "Mazamet", "Gaillac", "Graulhet", "Castelsarrasin",
    "Moissac", "Muret", "Colomiers", "Tournefeuille", "Blagnac",
    "Balma", "Cugnaux", "Pamiers", "Saint-Girons", "Saint-Gaudens",
    "Lourdes", "Bagnères-de-Bigorre", "Lannemezan", "Oloron-Sainte-Marie",
    "Orthez", "Mont-de-Marsan", "Dax", "Biarritz", "Anglet",
    "Saint-Jean-de-Luz", "Hendaye", "Arcachon", "La Teste-de-Buch",
    "Libourne", "Langon", "Blaye", "Lesparre-Médoc", "Bergerac",
    "Sarlat-la-Canéda", "Nontron", "Marmande", "Villeneuve-sur-Lot",
    "Nérac", "Condom", "Fleurance", "Mirande", "Saintes", "Rochefort",
    "Royan", "Jonzac", "Saint-Jean-d'Angély", "Cognac", "Confolens",
    "Bressuire", "Parthenay", "Thouars", "Châtellerault", "Montmorillon",
    "Bellac", "Rochechouart", "Ussel", "Montceau-les-Mines",
    "Le Creusot", "Autun", "Louhans", "Charolles", "Beaune",
    "Montbard", "Avallon", "Sens", "Joigny", "Cosne-Cours-sur-Loire",
    "Clamecy", "Château-Chinon", "Decize", "Lunéville", "Toul",
    "Briey", "Longwy", "Pont-à-Mousson", "Commercy", "Saint-Mihiel",
    "Remiremont", "Neufchâteau", "Gérardmer", "Saint-Avold",
    "Sarrebourg", "Château-Salins", "Wissembourg", "Saverne",
    "Molsheim", "Obernai", "Erstein", "Guebwiller", "Thann",
    "Altkirch", "Saint-Louis", "Ribeauvillé", "Vitry-le-François",
    "Sainte-Menehould", "Rethel", "Vouziers", "Revin", "Givet",
    "Bar-sur-Aube", "Romilly-sur-Seine", "Nogent-sur-Seine",
    "Langres", "Saint-Dizier", "Château-Thierry", "Vervins",
    "Chauny", "Tergnier", "Hirson", "Clermont", "Senlis", "Creil",
    "Noyon", "Méru", "Montdidier", "Péronne", "Albert", "Doullens",
    "Montreuil-sur-Mer", "Saint-Omer", "Béthune", "Bruay-la-Buissière",
    "Hénin-Beaumont", "Avesnes-sur-Helpe", "Fourmies", "Le Cateau-Cambrésis",
    "Caudry", "Denain", "Saint-Amand-les-Eaux", "Bailleul", "Bergues",
    "Gravelines", "Grande-Synthe", "Neufchâtel-en-Bray", "Yvetot",
    "Bolbec", "Lillebonne", "Elbeuf", "Louviers", "Vernon", "Les Andelys",
    "Gisors", "Bernay", "Pont-Audemer", "Honfleur", "Deauville",
    "Trouville-sur-Mer", "Cabourg", "Ouistreham", "Falaise", "Vire",
    "Flers", "Argentan", "L'Aigle", "Mortagne-au-Perche", "Coutances",
    "Carentan-les-Marais", "Valognes", "Barneville-Carteret",
    # Corse
    "Porto-Vecchio", "Calvi", "Corte", "Propriano", "Bonifacio",
    # Outre-mer (avec précision de géocodage)
    ("Pointe-à-Pitre", "Pointe-à-Pitre, Guadeloupe"),
    ("Basse-Terre", "Basse-Terre, Guadeloupe"),
    ("Baie-Mahault", "Baie-Mahault, Guadeloupe"),
    ("Le Gosier", "Le Gosier, Guadeloupe"),
    ("Sainte-Anne", "Sainte-Anne, Guadeloupe"),
    ("Le Moule", "Le Moule, Guadeloupe"),
    ("Fort-de-France", "Fort-de-France, Martinique"),
    ("Le Lamentin", "Le Lamentin, Martinique"),
    ("Schoelcher", "Schoelcher, Martinique"),
    ("Le Robert", "Le Robert, Martinique"),
    ("Saint-Joseph", "Saint-Joseph, La Réunion"),
    ("Cayenne", "Cayenne, Guyane"),
    ("Kourou", "Kourou, Guyane"),
    ("Saint-Laurent-du-Maroni", "Saint-Laurent-du-Maroni, Guyane"),
    ("Matoury", "Matoury, Guyane"),
    ("Rémire-Montjoly", "Rémire-Montjoly, Guyane"),
    ("Maripasoula", "Maripasoula, Guyane"),
    ("Saint-Georges-de-l'Oyapock", "Saint-Georges, Guyane"),
    ("Saint-Denis de La Réunion", "Saint-Denis, La Réunion"),
    ("Saint-Paul", "Saint-Paul, La Réunion"),
    ("Saint-Pierre de La Réunion", "Saint-Pierre, La Réunion"),
    ("Le Tampon", "Le Tampon, La Réunion"),
    ("Saint-André", "Saint-André, La Réunion"),
    ("Saint-Benoît", "Saint-Benoît, La Réunion"),
    ("Saint-Leu", "Saint-Leu, La Réunion"),
    ("Le Port", "Le Port, La Réunion"),
    ("Mamoudzou", "Mamoudzou, Mayotte"),
    ("Koungou", "Koungou, Mayotte"),
    ("Dzaoudzi", "Dzaoudzi, Mayotte"),
    ("Nouméa", "Nouméa, Nouvelle-Calédonie"),
    ("Dumbéa", "Dumbéa, Nouvelle-Calédonie"),
    ("Mont-Dore", "Mont-Dore, Nouvelle-Calédonie"),
    ("Koné", "Koné, Nouvelle-Calédonie"),
    ("Papeete", "Papeete, Polynésie française"),
    ("Faa'a", "Faa'a, Polynésie française"),
    ("Punaauia", "Punaauia, Polynésie française"),
    ("Mata-Utu", "Mata-Utu, Wallis-et-Futuna"),
]

# Noms trop ambigus pour le texte libre (titre / chapô) :
# acceptés uniquement via les tags de l'article.
RISKY_IN_TEXT = {
    # Départements homonymes de noms communs, fleuves, mots courants
    "Nord", "Somme", "Loire", "Marne", "Orne", "Eure", "Aisne", "Oise",
    "Var", "Ain", "Cher", "Indre", "Manche", "Mayenne", "Meuse",
    "Moselle", "Vienne", "Aube", "Lot", "Sarthe", "Yonne", "Doubs",
    "Drôme", "Isère", "Rhône", "Aude", "Nièvre", "Creuse", "Allier",
    "Gard", "Gers", "Loiret", "Jura", "Landes", "Savoie", "Vendée",
    "Vaucluse", "Hérault", "Tarn", "Cantal", "Charente", "Corrèze",
    # Villes homonymes de mots courants ou trop courtes
    "Tours", "Lens", "Fontaine", "Clermont", "Vienne", "Sens",
    "Valence", "Fleurance", "Albert", "Bondy",
    # "Saint-Denis", "Saint-Pierre", "Saint-Paul", "Sainte-Anne" :
    # multi-homonymes métropole/outre-mer → tags uniquement
    "Saint-Denis", "Saint-Pierre", "Saint-Paul", "Sainte-Anne",
    "Saint-André", "Saint-Benoît", "Saint-Leu", "Le Port", "Saint-Joseph",
    "Saint-Louis", "Le Moule", "Le Gosier", "Le Robert",
}


def build_gazetteer():
    """Retourne une liste de dicts triée par longueur de nom décroissante
    (pour matcher 'Seine-Saint-Denis' avant 'Seine' ou 'Saint-Denis')."""
    entries = []

    def add(name, query, cat):
        entries.append({
            "name": name,
            "query": query,
            "cat": cat,
            "risky": name in RISKY_IN_TEXT,
        })

    for r in REGIONS:
        add(r, f"{r}, France", "region")
    for t in TERRITOIRES_OUTREMER:
        add(t, t, "territoire")
    for d in DEPARTEMENTS:
        add(d, f"{d}, France", "departement")
    for v in VILLES:
        if isinstance(v, tuple):
            add(v[0], v[1], "ville")
        else:
            add(v, f"{v}, France", "ville")

    entries.sort(key=lambda e: len(e["name"]), reverse=True)
    return entries


GAZETTEER = build_gazetteer()
