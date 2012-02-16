# Copyright 2010, Red Hat, Inc
# James Bowes <jbowes@redhat.com>
# Alex Wood <awood@redhat.com>
# Seth Vidal <skvidal@fedoraproject.org>

# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# TODOS:
# - config_dict handling
# - permanent config changes
# - better _makeresults() that doesn't make me kinda hurl and makes the output more sensible


import func_module
from codes import FuncException

# XXX Use internal yum callback or write a useful one.
class DummyCallback(object):

    def event(self, state, data=None):
        pass

def _makeresults(tsInfo):
    results = ''
    for pkg in tsInfo:
        # FIXME obviously much more should happen here :)
        if pkg.ts_state:
            results += '%s\n' % pkg

    return results

def _multiActions(action_tuples, config_dict={}, **kwargs):
    #action tuple is action name(install/remove/erase/update) + item list
    import yum
    ayum = yum.YumBase()
    ayum.doRepoSetup()
    ayum.doLock()
    results = ''
    for (action, items) in action_tuples:
        if type(items) == type([]):
            pkglist = []
            for p in items:
                pkglist.extend(p.split(' '))
        else:
            if items:
                pkglist = items.split(' ')
            else:
                pkglist = []

        if len(pkglist) == 0 and action not in ('update', 'upgrade'):
            raise FuncException("%s requires at least one pkg" % action)
        
        results += 'command: %s %s\n' % (action, ' '.join(pkglist))
        if pkglist:
            for p in pkglist:
                tx_mbrs = []
                if action == 'install':
                    tx_mbrs = ayum.install(pattern=p)
                elif action in ('remove', 'erase'):
                    tx_mbrs = ayum.remove(pattern=p)

                elif action in ('update', 'upgrade'):
                    tx_mbrs = ayum.update(pattern=p)

                if not tx_mbrs:
                    results += "No %s matched for %s\n" % (action, p)

        else:
            ayum.update()
    try:
        ayum.buildTransaction()
        ayum.processTransaction(callback=DummyCallback())
    finally:
        results += _makeresults(ayum.tsInfo)
        ayum.closeRpmDB()
        ayum.doUnlock()
    return results
    
def _singleAction(action, items=[], config_dict={}, **kwargs):
    return _multiActions([(action, items)], config_dict, *kwargs)

class Yum(func_module.FuncModule):

    version = "0.0.1"
    api_version = "0.1.0"
    description = "Package updates through yum."

    from yum import __version__ as yumversion
    yvertuple = yumversion.split('.')
    if int(yvertuple[0]) == 3 and int(yvertuple[2]) >= 25:
        def rpmdbVersion(self, **kwargs):
            import yum
            ayum = yum.YumBase()
            versionlist = ayum.rpmdb.simpleVersion(main_only=True)
            version = versionlist[0]
            return versionlist

    def update(self, pkg=None, config_dict={}):
        return _singleAction('update', items=pkg, config_dict=config_dict)

    def install(self, pkg=None, config_dict={}):
        return _singleAction('install', items=pkg, config_dict=config_dict)

    def remove(self, pkg=None, config_dict={}):
        return _singleAction('remove', items=pkg, config_dict=config_dict)

    def multiple(self, cmdlist=[], config_dict={}):
        """take multiple commands as a single transaction - equiv of yum shell"""
        action_tuples = [] # it's a list of tuples, yes
        for c in cmdlist:
            cmd  = c.split()[0]
            items = c.split()[1:]
            action_tuples.append((cmd, items))
        return _multiActions(action_tuples, config_dict={})

    def get_package_lists(self, pkgspec='installed,available,obsoletes,updates,extras', config_dict={}):
        import yum
        ayum = yum.YumBase()
        ayum.doRepoSetup()
        resultsdict = {}
        pkgspec = pkgspec.replace(',',' ')
        pkgtypes = pkgspec.split(' ')
        for pkgtype in pkgtypes:
            pkgtype = pkgtype.strip()
            obj = ayum.doPackageLists(pkgnarrow=pkgtype)
            if hasattr(obj, pkgtype):
                thislist = getattr(obj, pkgtype)
                output_list = sorted(map(str, thislist))
                resultsdict[pkgtype] = output_list

        return resultsdict

    def check_update(self, filter=[], repo=None):
        """Returns a list of packages due to be updated
           You can specify a filter using the standard yum wildcards
        """
        # parsePackages expects a list and doesn't react well if you send in a plain string with a wildcard in it
        # (the string is broken into a list and one of the list elements is "*" which matches every package)
        if type(filter) not in [list, tuple]:
            filter = [filter]

        import yum
        ayum = yum.YumBase()
        ayum.doConfigSetup()
        ayum.doTsSetup()
        if repo is not None:
            ayum.repos.enableRepo(repo)

        pkg_list = ayum.doPackageLists('updates').updates

        if filter:
            # exactmatch are all the packages with exactly the same name as one in the filter list
            # matched are all the packages that matched under any wildcards
            # unmatched are all the items in the filter list that didn't match anything
            exactmatch, matched, unmatched = yum.packages.parsePackages(pkg_list, filter)
            pkg_list = exactmatch + matched

        return map(str, pkg_list)

    def grep(self, word):
        """
        Grep info from module
        """
        results = {self.check_update:[]}
        update_res = self.check_update()
        results[self.check_update].extend([res for res in update_res if res.lower().find(word)!=-1])

        return results
    grep = func_module.findout(grep)

    def register_method_args(self):
        """
        Implementing the argument getter
        """

        return{
                'update':{
                    'args':{
                        'pkg':{
                            'type':'string',
                            'optional':True,
                            'description':"The yum pattern for updating package"
                            }
                        },
                    'description':"Updating system according to a specified pattern"
                    },
                'install':{
                    'args':{
                        'pkg':{
                            'type':'string',
                            'optional':False,
                            'description':"The yum pattern for installing package"
                            }
                        },
                    'description':"install package(s) according to a specified pattern"
                    },
                'remove':{
                    'args':{
                        'pkg':{
                            'type':'string',
                            'optional':False,
                            'description':"The yum pattern for removing package"
                            }
                        },
                    'description':"remove package(s) according to a specified pattern"
                    },
                'check_update':{
                    'args':{
                        'filter':{
                            'type':'list',
                            'optional':True,
                            'description':"A list of what you want to update"
                            },
                        'repo':{
                            'type':'string',
                            'optional':True,
                            'description':'Repo name to use for that update'
                            }
                        },
                    'description':"Cheking for updates with supplied filter patterns and repo"
                    }
                }
