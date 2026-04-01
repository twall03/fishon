-- ============================================
-- 007: Seed Canonical Species and Aliases
-- ============================================
-- Note: alias_lower is auto-generated as LOWER(alias), so we only need
-- one casing per unique string. "Rainbow Trout" covers "rainbow trout" lookups.

-- Clean slate (idempotent — safe if partial data exists from failed prior run)
DELETE FROM species_aliases;
DELETE FROM species;

-- Insert canonical species
INSERT INTO species (id, common_name, scientific_name, species_group) VALUES
    (gen_random_uuid(), 'Rainbow Trout', 'Oncorhynchus mykiss', 'trout'),
    (gen_random_uuid(), 'Brown Trout', 'Salmo trutta', 'trout'),
    (gen_random_uuid(), 'Brook Trout', 'Salvelinus fontinalis', 'trout'),
    (gen_random_uuid(), 'Cutthroat Trout', 'Oncorhynchus clarkii', 'trout'),
    (gen_random_uuid(), 'Lake Trout', 'Salvelinus namaycush', 'trout'),
    (gen_random_uuid(), 'Tiger Trout', NULL, 'trout'),
    (gen_random_uuid(), 'Splake', NULL, 'trout'),
    (gen_random_uuid(), 'Golden Trout', 'Oncorhynchus aguabonita', 'trout'),
    (gen_random_uuid(), 'Bonneville Cutthroat Trout', 'Oncorhynchus clarkii utah', 'trout'),
    (gen_random_uuid(), 'Bear Lake Cutthroat Trout', NULL, 'trout'),
    (gen_random_uuid(), 'Kokanee Salmon', 'Oncorhynchus nerka', 'salmon'),
    (gen_random_uuid(), 'Chinook Salmon', 'Oncorhynchus tshawytscha', 'salmon'),
    (gen_random_uuid(), 'Atlantic Salmon', 'Salmo salar', 'salmon'),
    (gen_random_uuid(), 'Largemouth Bass', 'Micropterus salmoides', 'bass'),
    (gen_random_uuid(), 'Smallmouth Bass', 'Micropterus dolomieu', 'bass'),
    (gen_random_uuid(), 'Striped Bass', 'Morone saxatilis', 'bass'),
    (gen_random_uuid(), 'White Bass', 'Morone chrysops', 'bass'),
    (gen_random_uuid(), 'Wiper', NULL, 'bass'),
    (gen_random_uuid(), 'Walleye', 'Sander vitreus', 'walleye'),
    (gen_random_uuid(), 'Sauger', 'Sander canadensis', 'walleye'),
    (gen_random_uuid(), 'Yellow Perch', 'Perca flavescens', 'panfish'),
    (gen_random_uuid(), 'Bluegill', 'Lepomis macrochirus', 'panfish'),
    (gen_random_uuid(), 'Green Sunfish', 'Lepomis cyanellus', 'panfish'),
    (gen_random_uuid(), 'Black Crappie', 'Pomoxis nigromaculatus', 'panfish'),
    (gen_random_uuid(), 'White Crappie', 'Pomoxis annularis', 'panfish'),
    (gen_random_uuid(), 'Channel Catfish', 'Ictalurus punctatus', 'catfish'),
    (gen_random_uuid(), 'Blue Catfish', 'Ictalurus furcatus', 'catfish'),
    (gen_random_uuid(), 'Flathead Catfish', 'Pylodictis olivaris', 'catfish'),
    (gen_random_uuid(), 'Northern Pike', 'Esox lucius', 'pike'),
    (gen_random_uuid(), 'Tiger Muskie', NULL, 'pike'),
    (gen_random_uuid(), 'Muskellunge', 'Esox masquinongy', 'pike'),
    (gen_random_uuid(), 'Mountain Whitefish', 'Prosopium williamsoni', 'other'),
    (gen_random_uuid(), 'Bonneville Cisco', 'Prosopium gemmifer', 'other'),
    (gen_random_uuid(), 'Common Carp', 'Cyprinus carpio', 'carp'),
    (gen_random_uuid(), 'Grass Carp', 'Ctenopharyngodon idella', 'carp');

-- Rainbow Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Rainbow Trout'), ('rainbow'), ('rainbows'), ('bows'), ('RBT'), ('bow')) AS a(alias)
WHERE s.common_name = 'Rainbow Trout';

-- Brown Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Brown Trout'), ('brown'), ('browns'), ('brownie'), ('brownies')) AS a(alias)
WHERE s.common_name = 'Brown Trout';

-- Brook Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Brook Trout'), ('brook'), ('brookie'), ('brookies'), ('speckled trout')) AS a(alias)
WHERE s.common_name = 'Brook Trout';

-- Cutthroat Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Cutthroat Trout'), ('cutthroat'), ('cutts'), ('cutt'), ('cuts')) AS a(alias)
WHERE s.common_name = 'Cutthroat Trout';

-- Lake Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Lake Trout'), ('laker'), ('lakers'), ('mackinaw')) AS a(alias)
WHERE s.common_name = 'Lake Trout';

-- Tiger Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Tiger Trout'), ('tiger'), ('tigers')) AS a(alias)
WHERE s.common_name = 'Tiger Trout';

-- Splake aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Splake')) AS a(alias)
WHERE s.common_name = 'Splake';

-- Golden Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Golden Trout'), ('golden'), ('goldens')) AS a(alias)
WHERE s.common_name = 'Golden Trout';

-- Bonneville Cutthroat Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Bonneville Cutthroat Trout'), ('bonneville cutthroat'), ('BCT'), ('bonneville cutt')) AS a(alias)
WHERE s.common_name = 'Bonneville Cutthroat Trout';

-- Bear Lake Cutthroat Trout aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Bear Lake Cutthroat Trout'), ('bear lake cutthroat'), ('bear lake cutt')) AS a(alias)
WHERE s.common_name = 'Bear Lake Cutthroat Trout';

-- Kokanee Salmon aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Kokanee Salmon'), ('kokanee'), ('kokes'), ('kok')) AS a(alias)
WHERE s.common_name = 'Kokanee Salmon';

-- Chinook Salmon aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Chinook Salmon'), ('chinook'), ('king salmon'), ('king')) AS a(alias)
WHERE s.common_name = 'Chinook Salmon';

-- Atlantic Salmon aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Atlantic Salmon'), ('atlantic')) AS a(alias)
WHERE s.common_name = 'Atlantic Salmon';

-- Largemouth Bass aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Largemouth Bass'), ('largemouth'), ('largies'), ('LMB'), ('bucket mouth')) AS a(alias)
WHERE s.common_name = 'Largemouth Bass';

-- Smallmouth Bass aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Smallmouth Bass'), ('smallmouth'), ('smallies'), ('SMB'), ('bronzeback')) AS a(alias)
WHERE s.common_name = 'Smallmouth Bass';

-- Striped Bass aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Striped Bass'), ('striper'), ('stripers'), ('rockfish')) AS a(alias)
WHERE s.common_name = 'Striped Bass';

-- Wiper aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Wiper'), ('wipers'), ('hybrid striper'), ('hybrid striped bass')) AS a(alias)
WHERE s.common_name = 'Wiper';

-- Walleye aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Walleye'), ('walleyes'), ('eyes')) AS a(alias)
WHERE s.common_name = 'Walleye';

-- Yellow Perch aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Yellow Perch'), ('perch')) AS a(alias)
WHERE s.common_name = 'Yellow Perch';

-- Bluegill aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Bluegill'), ('gills'), ('bream'), ('sunfish')) AS a(alias)
WHERE s.common_name = 'Bluegill';

-- Black Crappie aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Black Crappie'), ('crappie'), ('slab'), ('slabs')) AS a(alias)
WHERE s.common_name = 'Black Crappie';

-- Channel Catfish aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Channel Catfish'), ('channel cat'), ('catfish'), ('cats')) AS a(alias)
WHERE s.common_name = 'Channel Catfish';

-- Northern Pike aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Northern Pike'), ('pike'), ('northern'), ('northerns'), ('jackfish')) AS a(alias)
WHERE s.common_name = 'Northern Pike';

-- Tiger Muskie aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Tiger Muskie'), ('tiger musky'), ('muskie'), ('musky')) AS a(alias)
WHERE s.common_name = 'Tiger Muskie';

-- Common Carp aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Common Carp'), ('carp')) AS a(alias)
WHERE s.common_name = 'Common Carp';

-- Mountain Whitefish aliases
INSERT INTO species_aliases (id, species_id, alias)
SELECT gen_random_uuid(), s.id, a.alias
FROM species s,
LATERAL (VALUES ('Mountain Whitefish'), ('whitefish'), ('whitey')) AS a(alias)
WHERE s.common_name = 'Mountain Whitefish';
