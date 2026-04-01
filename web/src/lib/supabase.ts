import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type WaterBody = {
  id: string;
  name: string;
  state: string;
  county: string;
  type: string;
  coordinates: string; // PostGIS POINT
  latitude: number;
  longitude: number;
  elevation_ft: number | null;
  surface_acres: number | null;
  has_stocking: boolean;
  has_flow_data: boolean;
  has_level_data: boolean;
  status: string;
};

export type StockingEvent = {
  id: string;
  water_body_id: string;
  species_raw: string;
  quantity: number | null;
  date: string;
  source_agency: string;
  source_url: string;
};

export type Condition = {
  id: string;
  water_body_id: string;
  flow_cfs: number | null;
  level_ft: number | null;
  temp_f: number | null;
  timestamp: string;
  gauge_id: string;
  source: string;
};

export type WeatherForecast = {
  id: string;
  water_body_id: string;
  forecast_date: string;
  temp_high_f: number | null;
  temp_low_f: number | null;
  wind_mph: number | null;
  precip_chance: number | null;
  summary: string | null;
  fetched_at: string;
};

export type WaterBodySpecies = {
  id: string;
  water_body_id: string;
  species_id: string;
  is_stocked: boolean;
  abundance: string | null;
  popular_methods: string[] | null;
  popular_baits: string[] | null;
  popular_lures: string[] | null;
  popular_flies: string[] | null;
  best_season: string | null;
  tips: string | null;
  species: { common_name: string };
};

export async function getWaterBodies(state: string = 'UT') {
  const { data, error } = await supabase
    .rpc('get_water_bodies_with_coords', { p_state: state });

  if (error) {
    // Fallback: direct query
    const { data: fallback } = await supabase
      .from('water_bodies')
      .select('*')
      .eq('state', state);
    return fallback || [];
  }
  return data || [];
}

export async function getWaterBodyDetail(id: string) {
  const [wb, stocking, conditions, weather, species] = await Promise.all([
    supabase.from('water_bodies').select('*').eq('id', id).single(),
    supabase.from('stocking_events').select('*').eq('water_body_id', id).order('date', { ascending: false }).limit(10),
    supabase.from('conditions').select('*').eq('water_body_id', id).order('timestamp', { ascending: false }).limit(1),
    supabase.from('weather_forecasts').select('*').eq('water_body_id', id).order('forecast_date').limit(5),
    supabase.from('water_body_species').select('*, species(common_name)').eq('water_body_id', id),
  ]);

  return {
    waterBody: wb.data,
    stocking: stocking.data || [],
    conditions: conditions.data?.[0] || null,
    weather: weather.data || [],
    species: species.data || [],
  };
}

export async function searchWaterBodies(query: string, state: string = 'UT') {
  const { data } = await supabase
    .from('water_body_aliases')
    .select('water_body_id, alias, water_bodies!inner(id, name, state, type, county)')
    .ilike('alias', `%${query}%`)
    .limit(20);

  return data || [];
}
