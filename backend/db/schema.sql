create table categorias (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  nombre text not null,
  tipo text not null check (tipo in ('solicitud', 'incidente')),
  descripcion text not null,
  quien_reporta text not null
);

create table tickets (
  id uuid primary key default gen_random_uuid(),
  titulo text not null,
  descripcion text not null,
  categoria_id uuid not null references categorias (id),
  tags text[] not null default '{}',
  impacto text not null check (impacto in ('alto', 'medio', 'bajo')),
  urgencia text not null check (urgencia in ('alta', 'media', 'baja')),
  prioridad text check (prioridad in ('P1', 'P2', 'P3', 'P4')),
  estado text not null default 'abierto' check (estado in ('abierto', 'en_progreso', 'resuelto', 'cerrado')),
  nivel text not null default 'N1' check (nivel in ('N1', 'N2', 'N3')),
  escalamiento_jerarquico text check (escalamiento_jerarquico in ('gerente_operaciones', 'direccion_comercial')),
  solicitante text not null,
  vence_respuesta_en timestamptz,
  vence_resolucion_en timestamptz,
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table comentarios (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references tickets (id) on delete cascade,
  autor text not null,
  autor_rol text not null check (autor_rol in ('solicitante', 'agente')),
  contenido text not null,
  interno boolean not null default false,
  creado_en timestamptz not null default now()
);

create index tickets_estado_idx on tickets (estado);
create index tickets_prioridad_idx on tickets (prioridad);
create index tickets_nivel_idx on tickets (nivel);
create index tickets_categoria_id_idx on tickets (categoria_id);
create index comentarios_ticket_id_idx on comentarios (ticket_id);

create function set_actualizado_en() returns trigger as $$
begin
  new.actualizado_en = now();
  return new;
end;
$$ language plpgsql;

create trigger tickets_set_actualizado_en
before update on tickets
for each row execute function set_actualizado_en();

alter table categorias enable row level security;
alter table tickets enable row level security;
alter table comentarios enable row level security;
