import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import {
  ILauncher,
} from "@jupyterlab/launcher";

import { ICommandPalette, MainAreaWidget } from '@jupyterlab/apputils';

import { Widget, Menu } from '@lumino/widgets';

import { toArray } from '@lumino/algorithm';

import { IMainMenu } from '@jupyterlab/mainmenu';


/**
 * Initialization data for the naasai extension.
 */

// Create a blank content widget inside of a MainAreaWidget
var content: Widget;
var widget: MainAreaWidget;

function initWidget() {
  content = new Widget();
  widget = new MainAreaWidget({ content });
  widget.id = 'naasai';
  widget.title.label = 'Naas manager';
  widget.title.closable = true;
    

  // Add an image element to the content
  let ifrm = document.createElement('iframe');
  content.node.appendChild(ifrm);
  ifrm.setAttribute('src', window.location.href.replace(/\/lab.*/g, '/naas'))
  ifrm.setAttribute('style', "width:100%;height:100%;")
}

async function getJupyterConfig() {

  let jupyterConfigElement: HTMLElement | null = document.getElementById('jupyter-config-data')

  if (jupyterConfigElement == null) {
    return 'Unknown'
  }

  let jupyterConfig = JSON.parse(jupyterConfigElement.innerHTML)
  console.log('jupyterConfig')
  console.log(jupyterConfig)

  return jupyterConfig
}

async function injectTypeform() {

  let jupyterConfig = await getJupyterConfig()
  let username = jupyterConfig['hubUser'] || 'local'
  let forms_to_show_to_user = await fetch(`https://typeform-handler.live.kn.naas.ai/todo/${username}`).then((response) => response.json());
  console.log('Forms to show to users')
  console.log(forms_to_show_to_user)


  if (forms_to_show_to_user.length > 0) {
    const form_id = forms_to_show_to_user[0]
    let options = {
      width: 600,
      height: 600,
      iframeProps: {
        style: "position:absolute;width:100%;height:100%;"
      },
      hidden: {
        email: username
      },
      autoClose: 3000,
      onSubmit: () => {
        console.log('Submited');
      },
      onClose: (e:any) => {
        console.log('Closed');
      }
    }
  
    // @ts-ignore: Unreachable code error
    const { open, close, toggle, refresh } = window.tf.createPopup(form_id, options);
    
    open();
  }

};

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'naasai:plugin',
  autoStart: true,
  optional: [ISettingRegistry, ILauncher],
  requires: [ISettingRegistry, ICommandPalette, IMainMenu, ILauncher],
  activate: (app: JupyterFrontEnd, settingRegistry: ISettingRegistry | null, palette: ICommandPalette, mainMenu: IMainMenu, launcher: ILauncher | null) => {
    const { commands } = app;
    //eval('window.app = app');
    console.log('JupyterLab extension naasai is activated!');

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(settings => {
          console.log('naasai settings loaded:', settings.composite);
        })
        .catch(reason => {
          console.error('Failed to load settings for naasai.', reason);
        });
    }

  initWidget();

  const naasMenu = new Menu({ commands });

  naasMenu.title.label = '⚡ Naas';
  mainMenu.addMenu(naasMenu, { rank: 1000 });

  let naas_commands = [
    {
      command_name : 'naasai:open-manager',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Manager',
        execute: () => {
          if (!widget.isAttached) {
            // Attach the widget to the main work area if it's not there

            initWidget()
            app.shell.add(widget, 'main' ,{
              'rank': -100000,
              'activate': false
            });
            app.shell.activateById(widget.id);
          } else {
            // Activate the widget
            app.shell.activateById(widget.id);
          }
  
        }
      }
    },
    {
      command_name : 'naasai:open-upgrade',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Upgrade',
        execute: () => {
          window.open('https://www.naas.ai/pricing', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-documentation',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Documentation',
        execute: () => {
          window.open('https://docs.naas.ai', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-github',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Github',
        execute: () => {
          window.open('https://github.com/jupyter-naas', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-slack',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Slack',
        execute: () => {
          window.open('https://app.slack.com/client/T01E5188RNV', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-roadmap',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Roadmap',
        execute: () => {
          window.open('https://github.com/orgs/jupyter-naas/projects/4?fullscreen=true', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-youtube',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Youtube',
        execute: () => {
          window.open('https://www.youtube.com/channel/UCKKG5hzjXXU_rRdHHWQ8JHQ', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-linkedin',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'LinkedIn',
        execute: () => {
          window.open('https://www.linkedin.com/company/naas-ai/', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-twitter',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Twitter',
        execute: () => {
          window.open('https://twitter.com/JupyterNaas', '_blank');
        }
      }
    },
    {
      command_name : 'naasai:open-instagram',
      palette_category: 'Naas',
      add_menu: true,
      command: {
        label: 'Instagram',
        execute: () => {
          window.open('https://www.instagram.com/naaslife/', '_blank');
        }
      }
    }
  ]

  for (const idx in naas_commands) {
    const cmd = naas_commands[idx]

    app.commands.addCommand(cmd.command_name, cmd.command);

    if (cmd.palette_category != null) {
      // Add the command to the palette.
       palette.addItem({ command: cmd.command_name, category: cmd.palette_category });
    }
  }

  // Setup menu
  naasMenu.addItem({ command: naas_commands[0].command_name});
  naasMenu.addItem({ command: naas_commands[1].command_name});
  naasMenu.addItem({ command: naas_commands[2].command_name});
  naasMenu.addItem({ command: naas_commands[3].command_name});
  naasMenu.addItem({ command: naas_commands[4].command_name});
  naasMenu.addItem({ command: naas_commands[5].command_name});
  naasMenu.addItem({type: "separator"})
  naasMenu.addItem({ command: naas_commands[6].command_name});
  naasMenu.addItem({ command: naas_commands[7].command_name});
  naasMenu.addItem({ command: naas_commands[8].command_name});
  naasMenu.addItem({ command: naas_commands[9].command_name});


  app.restored.then(() => {
    console.log('restored')
    injectTypeform();

    if (toArray(app.shell.widgets('main')).length == 0) {
      app.commands.execute('naasai:open-manager');
      app.commands.execute('launcher:create');
      
      // Activate the widget
      app.shell.activateById(widget.id);
    }

    if (launcher) {
      let splitted_url = window.location.href.split('/')
      splitted_url[splitted_url.length-1] = 'static/favicons/favicon.ico'

      launcher.add({
        command: 'naasai:open-manager', 
        category: 'Notebook',
        kernelIconUrl: window.location.href.replace(/\/lab.*/g, '/static/favicons/favicon.ico'),
        rank: 100
      });
    }
  });

  app.started.then(function() {
    console.log('naasai started')
  })

  }
};

export default plugin;
