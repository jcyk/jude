drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  sender text not null,
  reciever text not null,
  'text' text not null,
  'date' date not null,
  recieved boolean not null
);

drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  pw_hash text not null
);

