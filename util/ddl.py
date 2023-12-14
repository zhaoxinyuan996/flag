d1 = '''
create table test (f1 int, f2 text, f3 int[], f4 text[], f5 json);
'''

# 用户表
d2 = '''
create table users (
id serial primary key, 

nickname text,
username text  not null, 
password text not null,
phone int,
sex int,

wechat_id text,
google_id text,
apple_id text,

signature text,
profile_picture text,
background_picture text,

create_time timestamp not null,
vip_deadline timestamp,
block_deadline timestamp,
alive_deadline timestamp,
belong text,
location text,
UNIQUE(username)
);
'''

# 关注表
d3 = '''
create table follow(
fans_id int not null,
star_id int not null,
primary key(fans_id, star_id)
);
'''
d4 = '''
CREATE INDEX fans_index ON follow(fans_id);
CREATE INDEX star_index ON follow(star_id);
'''

# 注销表
d5 = '''
create table sign_out_users (
user_id int primary key,
out_time timestamp not null
)
'''

# flag表
d6 = '''
create table flag (
id serial primary key,
user_id int not null,
location point not null,
content text,
type int,
is_open int not null,
create_time timestamp not null,
update_time timestamp not null,
pictures text[] not null
);
'''

d7 = '''
CREATE INDEX type_index ON flag(type);
CREATE INDEX is_open_index ON flag(is_open);
CREATE INDEX user_id_index ON flag(user_id);
CREATE INDEX flag_index ON flag USING GIST (location);
'''

# 评论表
d8 = '''
create table flag_comment(
id serial primary key,
flag_id int not null,
user_id int not null,
content text not null,
root_comment_id int,
location point not null,
prefix text,
comment_time timestamp not null
)
'''

d9 = '''
CREATE INDEX flag_comment_index ON flag_comment(flag_id);
CREATE INDEX comment_flag_comment_index ON flag_comment USING GIST (location);
'''
