-- Extract lat/lon from PostGIS geography for the frontend
CREATE OR REPLACE FUNCTION get_water_body_coords(p_state CHAR(2))
RETURNS TABLE(id UUID, lat FLOAT, lon FLOAT) AS $$
    SELECT
        wb.id,
        ST_Y(wb.coordinates::geometry) AS lat,
        ST_X(wb.coordinates::geometry) AS lon
    FROM water_bodies wb
    WHERE wb.state = p_state;
$$ LANGUAGE sql STABLE;
