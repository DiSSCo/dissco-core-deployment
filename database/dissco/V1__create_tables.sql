create table annotation
(
    id               text                     not null
        constraint annotation_pk
            primary key,
    version          integer                  not null,
    type             text                     not null,
    motivation       text                     not null,
    motivated_by     text,
    target_id        text                     not null,
    target           jsonb                    not null,
    body             jsonb                    not null,
    creator_id       text                     not null,
    creator          jsonb                    not null,
    created          timestamp with time zone not null,
    generator        jsonb                    not null,
    generated        timestamp with time zone not null,
    last_checked     timestamp with time zone not null,
    aggregate_rating jsonb,
    deleted_on       timestamp with time zone
);

create index annotation_id_creator_id_index
    on annotation (id, creator_id);

create index annotation_id_target_id_index
    on annotation (id, target_id);

create table mas_job_record
(
    job_id         uuid default uuid_generate_v4() not null
        constraint mas_job_record_pk
            primary key,
    state          text                            not null,
    creator_id     text                            not null,
    time_started   timestamp with time zone        not null,
    time_completed timestamp with time zone,
    annotations    jsonb,
    target_id      text                            not null
);

create index mas_job_record_created_idx
    on mas_job_record (time_started);

create index mas_job_record_job_id_index
    on mas_job_record (job_id);

create table digital_media_object
(
    id                      text                     not null
        constraint digital_media_object_pk
            primary key,
    version                 integer                  not null,
    type                    text                     not null,
    digital_specimen_id     text                     not null,
    media_url               text                     not null,
    created                 timestamp with time zone not null,
    last_checked            timestamp with time zone not null,
    deleted                 timestamp with time zone,
    data                    jsonb                    not null,
    original_data           jsonb                    not null
);

create index digital_media_object_id_idx
    on digital_media_object (id, media_url);

create unique index digital_media_object_id_version_url
    on digital_media_object (id, version, media_url);

create index digital_media_object_digital_specimen_id_url
    on digital_media_object (digital_specimen_id, media_url);

create table digital_specimen
(
    id                          text                        not null
        constraint digital_specimen_pk
            primary key,
    version                     integer                     not null,
    type                        text                        not null,
    midslevel                   smallint                    not null,
    physical_specimen_id        text                        not null,
    physical_specimen_type      text                        not null,
    specimen_name               text,
    organization_id             text                        not null,
    source_system_id            text                        not null,
    created                     timestamp with time zone    not null,
    last_checked                timestamp with time zone    not null,
    deleted                     timestamp with time zone,
    data                        jsonb                       not null,
    original_data               jsonb                       not null
);


create index digital_specimen_created_idx
    on digital_specimen (created);

create index digital_specimen_physical_specimen_id_idx
    on digital_specimen (physical_specimen_id);

create table mapping
(
    id                 text                     not null,
    version            integer                  not null,
    name               text                     not null,
    description        text,
    mapping            jsonb                    not null,
    created            timestamp with time zone not null,
    creator            text                     not null,
    deleted            timestamp with time zone,
    source_data_standard varchar                  not null,
    constraint new_mapping_pk
        primary key (id, version)
);


create table source_system
(
    id          text                                        not null
        constraint new_source_system_pkey
            primary key,
    name        text                                        not null,
    endpoint    text                                        not null,
    description text,
    created     timestamp with time zone                    not null,
    deleted     timestamp with time zone,
    mapping_id  text                                        not null,
    version     integer default 1                           not null,
    creator     text                                        not null
);

create table new_user
(
    id           text                     not null
        primary key,
    first_name   text,
    last_name    text,
    email        text,
    orcid        text,
    organization text,
    created      timestamp with time zone not null,
    updated      timestamp with time zone not null
);

create table machine_annotation_services
(
    id                            text                     not null
        primary key,
    version                       integer                  not null,
    name                          varchar                  not null,
    created                       timestamp with time zone not null,
    administrator                 text                     not null,
    container_image               text                     not null,
    container_image_tag           text                     not null,
    target_digital_object_filters jsonb,
    service_description           text,
    service_state                 text,
    source_code_repository        text,
    service_availability          text,
    code_maintainer               text,
    code_license                  text,
    dependencies                  text[],
    support_contact               text,
    sla_documentation             text,
    topicname                     text,
    maxreplicas                   integer,
    deleted_on                    timestamp with time zone
);