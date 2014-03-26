drop table if exists users;
create table users (
    id integer primary key autoincrement,
    name text not null,
    pw_hash text not null,
    email text
);

drop table if exists items;
create table items (
    id integer primary key autoincrement,
    user_id integer,
    content text not null,
    state text not null,
    added timestamp not null, -- time added
    foreign key(user_id) references users(id)
);
