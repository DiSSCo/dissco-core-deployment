create table handles
(
    handle      bytea   not null,
    idx         integer not null,
    type        bytea,
    data        bytea,
    ttl_type    smallint,
    ttl         integer,
    timestamp   bigint,
    refs        text,
    admin_read  boolean,
    admin_write boolean,
    pub_read    boolean,
    pub_write   boolean,
    primary key (handle, idx)
);

create index dataindex
    on handles (data);

create index handleindex
    on handles (handle);

create table nas
(
    na bytea not null
        primary key
);