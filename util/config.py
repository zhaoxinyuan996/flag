import os
import yaml

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml')) as c:
    config = yaml.load(c, yaml.Loader)

uri = 'postgresql://{}:{}@{}:{}/{}'.format(
        config['db'][config['env']]['user'],
        config['db'][config['env']]['passwd'],
        config['db'][config['env']]['host'],
        config['db'][config['env']]['port'],
        config['db'][config['env']]['db_name']
    )
dev = config['db'][config['env']] == 'dev'


if __name__ == '__main__':
    print(config)
