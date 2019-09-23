#/usr/bin/env python2.7
from fabric.api import run, task, parallel, env, local, put, execute, prefix, sudo
from fabric.context_managers import cd, settings, shell_env
from fabric import utils
from fabric.contrib.files import upload_template, exists, append, comment
import os.path
import getpass


WEBAPP_PORT = "8080"
UNIXUSER = "usman"
SERVER = ['ahmedu']

SCIPR_REPONAME = "SciPRecommender"
SCIPR_REPO =     "https://github.com/tf-dbis-uni-freiburg/SciPRecommender.git"
REPO_CLONE_DIR =    os.path.join("/home", UNIXUSER, SCIPR_REPONAME)
DJANGO_DIR =        os.path.join("/home", UNIXUSER, SCIPR_REPONAME, "Code", "MasterProject")
VENV_DIR =          os.path.join("/home", UNIXUSER, SCIPR_REPONAME, "Code", "webapp_venv")
VENV_ACTIVATE =     os.path.join("/home", UNIXUSER, SCIPR_REPONAME, "Code", "webapp_venv", "bin", "activate")
REQUIREMENTS_FILE = os.path.join(REPO_CLONE_DIR, "requirements.txt")


# You can preset those values, but don't commit it!!
# env.password = "secret"
# env.scipr_unixuser_pw = "secret"
# env.scipr_database_root_pw = "secret"
# env.scipr_django_admin_pw = "secret"

def _as_scipr():
    tmp_settings = {"user": UNIXUSER}
    if "scipr_unixuser_pw" in env and env.scipr_unixuser_pw is not None:
        print("env.scipr_unixuser_pw", env.scipr_unixuser_pw)
        tmp_settings["password"] = env.scipr_unixuser_pw

    return settings(**tmp_settings)

@task
def allow_password_auth():
    # needs to be a separate task, so that the changed env.hosts is taken into account
    comment("/etc/ssh/sshd_config", "^PasswordAuthentication no$", use_sudo=True)
    sudo("service ssh reload")

@task
def prod():
    env.user = UNIXUSER
    env.hosts = SERVER

    # we only need to call this when init
    env.scipr_call_on_init = prod_ssh

@task
def prod_ssh():
    if "password" not in env or not env.password:
        env.password = getpass.getpass("Password for {user}@{host}: ".format(user=env.user, host=env.hosts[0]))
    if "sudo_password" not in env or not env.sudo_password:
        env.sudo_password = env.password

    if "scipr_unixuser_pw" not in env or not env.scipr_unixuser_pw:
        env.scipr_unixuser_pw = getpass.getpass("Password for {user}@{host}: ".format(user=UNIXUSER, host=env.hosts[0]))


    # if not os.path.exists("./id_rsa") or not os.path.exists("./id_rsa.pub"):
    #     utils.abort('Please put a deploy key named "id_rsa" into the repo dir.')
    # env.scipr_ssh_identety = "./id_rsa"
    # env.scipr_ssh_identety_pub = "./id_rsa.pub"


@task
def update_system_package_manager():
    sudo("apt-get update")

@task
def setup_redis():
    query_redis_server = run("which redis-server", warn_only=True)
    if query_redis_server.failed:
        with cd("/tmp"):
            run("curl -O http://download.redis.io/redis-stable.tar.gz")
            run("tar xzvf redis-stable.tar.gz")
            with cd("redis-stable"):
                run("make")
                # run("make test")
                sudo("make install")
                sudo("mkdir -p /etc/redis")
                sudo("mkdir -p /var/lib/redis")
                sudo("mkdir -p /var/lib/redis")
    upload_template("configs/redis.conf.j2",
                    "/etc/redis/redis.conf", mode=0744, use_jinja=True, use_sudo=True,
                    context={"user": UNIXUSER})
    upload_template("configs/redis.service.j2",
                    "/etc/systemd/system/redis.service", mode=0744, use_jinja=True, use_sudo=True,
                    context={"user": UNIXUSER})
    sudo("chown " + UNIXUSER + ":" + UNIXUSER + " /var/lib/redis")
    sudo("systemctl start redis")



@task
def install_system_requiremtents():
    sudo("apt-get install -y " + " ".join(["libmysqlclient-dev",
                                               "python3-pip",
                                               "memcached",
                                               "supervisor",
                                               "python3-venv",
                                               "curl"]))


    sudo("python3 -m pip install mysqlclient")

    execute(install_nginx)

@task
def setup_user():
    if run("id {username}".format(username=UNIXUSER), warn_only=True).succeeded:
        return  # user already created

    sudo('adduser {username} --gecos "scipr user" --disabled-password'.format(username=UNIXUSER))
    # TODO password is printed in terminal. Bad thing.
    sudo('echo "{username}:{password}" | chpasswd'.format(username=UNIXUSER, password=env.scipr_unixuser_pw))

    with _as_scipr():
        run("mkdir -p .ssh")
        put(env.scipr_ssh_identety, remote_path="~/.ssh/id_rsa", mode=0600)
        key_text = open(os.path.expanduser(env.scipr_ssh_identety_pub)).read()
        append('~/.ssh/authorized_keys', key_text)

@task
def init_webapp(branchname=None):
    if branchname is None:
        branchname = "development"

    with _as_scipr():
        if not exists(REPO_CLONE_DIR):
            run("git clone {} {}".format(SCIPR_REPO, REPO_CLONE_DIR))
        else:
            with cd(REPO_CLONE_DIR):
                run("git fetch".format(SCIPR_REPO, REPO_CLONE_DIR))

        with cd(REPO_CLONE_DIR):
            run("git reset --hard")
            run("git checkout " + branchname)

        if not exists(VENV_DIR):
            run("python3.5 -m venv " + VENV_DIR)
        put("requirements.txt", REQUIREMENTS_FILE)
        with prefix("source " + VENV_ACTIVATE):
            run("pip install -r " + REQUIREMENTS_FILE)

        with cd(DJANGO_DIR):
            with prefix("source " + VENV_ACTIVATE):
                run("python ./manage.py migrate")

        upload_template("configs/gunicorn_start.j2", os.path.join(REPO_CLONE_DIR, "gunicorn_start"), mode=0744,
                        use_jinja=True, context={"clone_directory": REPO_CLONE_DIR, "webapp_directory": DJANGO_DIR})
        upload_template("configs/worker_start.j2", os.path.join(REPO_CLONE_DIR, "redis_fastqueue_start"), mode=0744,
                        use_jinja=True, context={"webapp_directory": DJANGO_DIR, "queue": "Fast"})
        upload_template("configs/worker_start.j2", os.path.join(REPO_CLONE_DIR, "redis_slowqueue_start"), mode=0744,
                        use_jinja=True, context={"webapp_directory": DJANGO_DIR, "queue": "Slow"})

        run("mkdir -p " + os.path.join(REPO_CLONE_DIR, "logs"))

@task
def config_supervisor():
    upload_template("configs/masterproject_webapp.j2",
                    "/etc/supervisor/conf.d/masterproject_webapp.conf", mode=0744, use_jinja=True, use_sudo=True,
                    context={"clone_directory": REPO_CLONE_DIR, "user": UNIXUSER})
    upload_template("configs/redis_worker.j2",
                    "/etc/supervisor/conf.d/redis_fastqueue.conf", mode=0744, use_jinja=True, use_sudo=True,
                    context={"clone_directory": REPO_CLONE_DIR, "user": UNIXUSER, "supervisor_name": "redis_fastqueue",
                             "log_file": "fast_queue_supervisor.log", "start_file": "redis_fastqueue_start"})
    sudo("service supervisor restart")

    # upload_template does not support setting the user to root in one step. We therefor upload it to /tmp, change
    # user/group and copy it to the target location while preserving the user/group.
    upload_template("configs/sudoers_supervisorctl_webapp.j2",
                    "/tmp/sudoers_supervisorctl_webapp", mode=0744, use_jinja=True,
                    context={"user": UNIXUSER})
    sudo("chown root:root /tmp/sudoers_supervisorctl_webapp")
    sudo("cp --preserve=ownership /tmp/sudoers_supervisorctl_webapp /etc/sudoers.d/sudoers_supervisorctl_webapp")
    sudo("rm /tmp/sudoers_supervisorctl_webapp")


@task
def install_nginx():
    query_nginx = run("dpkg -l nginx | grep nginx", warn_only=True)
    if query_nginx.succeeded and query_nginx.split()[0][1] == "i":
        return # nginx is already installed -> early return

    start_apache_again = False
    if sudo('sudo service apache2 status | grep "running"', warn_only=True).succeeded:
        # we can not install nginx when apache runs (assuming it uses port 80)
        start_apache_again = True
        sudo("sudo service apache2 stop")

    sudo("apt-get install -y nginx")

    # remove the default page. We can then start apache again
    if exists("/etc/nginx/sites-enabled/default"):
        sudo("rm /etc/nginx/sites-enabled/default")

    if start_apache_again:
        sudo("sudo service apache2 start")

@task
def config_nginx():
    upload_template("configs/nginx_masterproject_webapp.j2",
                    "/etc/nginx/sites-available/nginx_masterproject_webapp", mode=0744, use_jinja=True, use_sudo=True,
                    context={"clone_directory": REPO_CLONE_DIR,
                             "webapp_port": WEBAPP_PORT})

    if not exists("/etc/nginx/sites-enabled/nginx_masterproject_webapp"):
        sudo("ln -s /etc/nginx/sites-available/nginx_masterproject_webapp /etc/nginx/sites-enabled/nginx_masterproject_webapp")
    sudo("service nginx restart")

@task
def update(branchname='development'):
    if "scipr_call_on_init" in env:
        execute(env.scipr_call_on_init)

    sudo("/usr/bin/supervisorctl stop masterproject")
    sudo("/usr/bin/supervisorctl stop redis_fastqueue")

    with cd(REPO_CLONE_DIR):
        run("git reset --hard HEAD")
        run("git fetch")
        run("git checkout {}".format(branchname))
        run("git pull")

    with prefix("source " + VENV_ACTIVATE):
        run("pip install -r " + os.path.join(REPO_CLONE_DIR, "requirements.txt"))

    with cd(DJANGO_DIR):
        with prefix("source " + VENV_ACTIVATE):
            run("python ./manage.py migrate")

    sudo("/usr/bin/supervisorctl start masterproject")
    sudo("/usr/bin/supervisorctl start redis_fastqueue")

@task
def flower():
    with _as_scipr():

        with prefix("source " + VENV_ACTIVATE):
            run("pip install flower")

        with cd(DJANGO_DIR):
            with prefix("source " + VENV_ACTIVATE):
                run("celery -A masterproject_webapp flower")

@task
def init(branchname=None):
    if "scipr_call_on_init" in env:
        execute(env.scipr_call_on_init)

    execute(update_system_package_manager)
    execute(install_system_requiremtents)
    execute(setup_user)
    execute(setup_redis)
    execute(init_webapp, branchname)
    execute(config_supervisor)
    execute(config_nginx)
