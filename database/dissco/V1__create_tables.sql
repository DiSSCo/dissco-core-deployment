create table annotation
(
    id              text                     not null
        constraint annotation_pk
            primary key,
    version         integer                  not null,
    type            text                     not null,
    annotation_hash uuid,
    motivation      text                     not null,
    mjr_job_id      text,
    batch_id        uuid,
    creator         text                     not null,
    created         timestamp with time zone not null,
    modified        timestamp with time zone not null,
    last_checked    timestamp with time zone not null,
    tombstoned      timestamp with time zone,
    target_id       text                     not null,
    data            jsonb
);

create index annotation_id_creator_id_index
    on annotation (id, creator);

create index annotation_id_target_id_index
    on annotation (id, target_id);

create index annotation_hash_index
    on annotation (annotation_hash);


create type job_state as enum ('SCHEDULED', 'RUNNING', 'FAILED', 'COMPLETED', 'NOTIFICATION_FAILED', 'QUEUED');
create type mjr_target_type as enum ('DIGITAL_SPECIMEN', 'MEDIA_OBJECT');
create type error_code as enum ('TIMEOUT', 'DISSCO_EXCEPTION');
create type export_type as enum ('DOI_LIST', 'DWC_DP', 'DWCA');

create table mas_job_record
(
    job_id             text                     not null
        constraint mas_job_record_pk
            primary key,
    job_state          job_state                not null,
    mas_id             text,
    time_started       timestamp with time zone not null,
    time_completed     timestamp with time zone,
    annotations        jsonb,
    target_id          text                     not null,
    creator            text,
    target_type        mjr_target_type,
    batching_requested boolean,
    error              error_code,
    expires_on         timestamp with time zone not null,
    error_message      text
);

create index mas_job_record_created_idx
    on mas_job_record (time_started);

create index mas_job_record_job_id_index
    on mas_job_record (job_id);

create table digital_media_object
(
    id                  text                     not null
        constraint digital_media_object_pk
            primary key,
    version             integer                  not null,
    type                text,
    media_url           text                     not null,
    created             timestamp with time zone not null,
    last_checked        timestamp with time zone not null,
    deleted             timestamp with time zone,
    data                jsonb                    not null,
    original_data       jsonb                    not null,
    modified            timestamp with time zone
);

create index digital_media_object_id_idx
    on digital_media_object (id, media_url);

create unique index digital_media_object_id_version_url
    on digital_media_object (id, version, media_url);

create index digital_media_object_digital_specimen_id_url
    on digital_media_object (digital_specimen_id, media_url);

create table digital_specimen
(
    id                     text                     not null
        constraint digital_specimen_pk
            primary key,
    version                integer                  not null,
    type                   text                     not null,
    midslevel              smallint                 not null,
    physical_specimen_id   text                     not null,
    physical_specimen_type text                     not null,
    specimen_name          text,
    organization_id        text                     not null,
    source_system_id       text                     not null,
    created                timestamp with time zone not null,
    last_checked           timestamp with time zone not null,
    deleted                timestamp with time zone,
    data                   jsonb,
    original_data          jsonb,
    modified               timestamp with time zone
);


create index digital_specimen_created_idx
    on digital_specimen (created);

create index digital_specimen_physical_specimen_id_idx
    on digital_specimen (physical_specimen_id);

create table data_mapping
(
    id                    text                     not null,
    version               integer                  not null,
    name                  text                     not null,
    created               timestamp with time zone not null,
    modified              timestamp with time zone not null,
    tombstoned            timestamp with time zone,
    creator               text                     not null,
    mapping_data_standard varchar                  not null,
    data                  jsonb                    not null,
    constraint data_mapping_pk
        primary key (id, version)
);

create type translator_type as enum ('biocase', 'dwca');

create table source_system
(
    id              text                     not null
        primary key,
    version         integer default 1        not null,
    name            text                     not null,
    endpoint        text                     not null,
    created         timestamp with time zone not null,
    modified        timestamp with time zone not null,
    tombstoned      timestamp with time zone,
    mapping_id      text                     not null,
    creator         text                     not null,
    translator_type translator_type          not null,
    data            jsonb                    not null,
    dwc_dp_link     text,
    dwca_link       text,
    eml             bytea
);

create table machine_annotation_service
(
    id                     text                     not null
        constraint machine_annotation_services_pkey
            primary key,
    version                integer                  not null,
    name                   varchar                  not null,
    created                timestamp with time zone not null,
    modified               timestamp with time zone not null,
    tombstoned             timestamp with time zone,
    creator                text                     not null,
    container_image        text                     not null,
    container_image_tag    text                     not null,
    creative_work_state    text,
    source_code_repository text,
    service_availability   text,
    code_maintainer        text,
    code_license           text,
    support_contact        text,
    batching_permitted     boolean,
    time_to_live           integer default 86400    not null,
    data                   jsonb                    not null
);

create table translator_job_record
(
    job_id            uuid                     not null,
    job_state         job_state                not null,
    source_system_id  text                     not null,
    time_started      timestamp with time zone not null,
    time_completed    timestamp with time zone,
    processed_records integer,
    error             error_code,
    primary key (job_id, source_system_id)
);

create table export_queue
(
    id                   uuid                     not null
        constraint export_queue_pk
            primary key,
    params               jsonb                    not null,
    creator              text                     not null,
    job_state            job_state                not null,
    time_scheduled       timestamp with time zone not null,
    time_started         timestamp with time zone,
    time_completed       timestamp with time zone,
    export_type          export_type              not null,
    hashed_params        uuid                     not null,
    destination_email    text                     not null,
    download_link        text,
    target_type          text                     not null,
    is_source_system_job boolean                  not null
);

create table annotation_batch_record
(
    id                   uuid                     not null
        constraint annotation_batch_pk
            primary key,
    creator              text                     not null,
    created              timestamp with time zone not null,
    last_updated         timestamp with time zone,
    job_id               text,
    batch_quantity       bigint,
    parent_annotation_id text
);

create type collection_type as enum ('REFERENCE_COLLECTION', 'COMMUNITY_COLLECTION');

create table virtual_collection
(
    id              text                     not null
        primary key,
    version         integer default 1        not null,
    name            text                     not null,
    collection_type collection_type         not null,
    endpoint        text                     not null,
    created         timestamp with time zone not null,
    modified        timestamp with time zone not null,
    tombstoned      timestamp with time zone,
    creator         text                     not null,
    data            jsonb                    not null
);