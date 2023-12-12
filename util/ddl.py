d1 = '''
create table test (f1 int, f2 text, f3 int[], f4 text[], f5 json);
'''

d2 = '''
create table users (
id serial, 

nickname text,
username text primary key not null, 
password text not null,
phone int,

wechat_id text,
google_id text,
apple_id text,

signature text,
profile_picture text,
background_picture text,

create_time timestamp not null,
vip_deadline timestamp
);
'''