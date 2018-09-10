# table creation

#CNL

Create Table cnltmp (
  id string primary key,
  uf string,
  cnl string,
  cnl_cod string,
  place string,
  province string,
  tarifation_cod string,
  prefix string,
  operator string,
  initial_phone integer,
  final_phone integer,
  geoposition array(string),
  cnl_local_area_cod  string,
  ddd integer,
  operator_id string,
  is_mobile boolean,
  created_at timestamp
)

Create table operator (
  id string primary key,
  name string,
  img_translate string
)

Create table ddd (
  id integer primary key,
  state string
)

Create table phone (
  id string primary key,
  operator string,
  portability_id integer,
  portability_type integer,
  action integer,
  new_spid integer,
  eot string,
  is_mobile boolean,
  activation_time timestamp,
  start_time timestamp,
  created_at timestamp,
  updated_at timestamp
)


Create table header (
  id string primary key,
  generated timestamp,
  number_of_items integer
)

Create table translateoperator (
  id string,
  name string,
  rn1 string,
  operator string,
  created_at timestamp
)