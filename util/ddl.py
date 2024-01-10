d1 = '''
create table test (f1 int, f2 text, f3 int[], f4 text[], f5 json);
'''

# 用户表
d2 = '''
create table users (
id uuid primary key, 

nickname text not null,
username text, 
password text,
phone int,
is_man bool,

signature text,
avatar_name text,
bg_avatar_name text,
flag_num int not null default 0,

create_time timestamp not null,
vip_deadline timestamp,
block_deadline timestamp,
alive_deadline timestamp,
belong text,
local text,
extend1 text,
extend2 text,
extend3 text
);

create index username_index on users using hash(username);
'''

# 第三方用户
d2_1 = '''
create table third_users (
id uuid primary key,
login_type text not null,
open_id text not null,
access_token text,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX login_type_index on third_users (login_type) WHERE login_type='wechat';
'''

# 关注表
d3 = '''
create table follow(
fans_id uuid not null,
star_id uuid not null,
primary key(fans_id, star_id),
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX fans_index ON follow(fans_id);
CREATE INDEX star_index ON follow(star_id);
'''

# 注销表
d4 = '''
create table sign_out_users (
user_id uuid primary key,
out_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
)
'''

# flag表
d5 = '''
create table flag (
id uuid primary key,
user_id uuid not null,
location geometry(geometry,4326) not null,
name text not null,
content text not null,
type int,
status int not null,
user_class int not null,
create_time timestamp not null,
update_time timestamp not null,
pictures text[] not null,
ico_name text not null,
dead_line timestamp,
extend3 text,
unique(location)
);


CREATE INDEX type_index ON flag(type);
CREATE INDEX is_open_index ON flag(is_open);
create index flag_user_id_index on flag using hash(user_id);
CREATE INDEX flag_location_index ON flag USING GIST (location);
'''

# 评论表
d6 = '''
create table flag_comment(
id serial primary key,
flag_id uuid not null,
user_id uuid not null,
content text not null,
root_comment_id int,
location geometry(geometry,4326),
show_distance bool not null default true,
prefix text,
comment_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX flag_comment_index ON flag_comment(flag_id);
CREATE INDEX root_comment_index ON flag_comment(root_comment_id);
'''

# 黑名单
d7 = '''
create table black_list(
user_id uuid not null,
black_id uuid not null,
update_time timestamp,
primary key(user_id, black_id),
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX user_black_index ON black_list(user_id);
'''

# 消息
d8 = '''
create table message(
id serial primary key,
type int not null,
send_id int not null,
receive_id int not null,
content text not null,
create_time timestamp not null,
extend1 text,
extend2 text,
extend3 text
);

CREATE INDEX receive_id_message_index ON message(receive_id);
'''

# 收藏表
d9 = '''
create table fav (
id serial primary key,
user_id uuid not null,
flag_id uuid not null,
create_time timestamp not null,
extend1 text,
extend2 text,
unique(user_id, flag_id)
);

CREATE INDEX fav_user_id_index on fav (user_id);
'''

# 系统消息
d10 = '''
create table notice (
id serial primary key,
version text not null,
user_class int not null,
title text not null,
content text not null,
create_time timestamp
)
'''