import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { ICommandPalette, MainAreaWidget } from '@jupyterlab/apputils';

import { Widget, Menu } from '@lumino/widgets';


import { IMainMenu } from '@jupyterlab/mainmenu';


/**
 * Initialization data for the naasai extension.
 */


const plugin: JupyterFrontEndPlugin<void> = {
  id: 'naasai:plugin',
  autoStart: true,
  optional: [ISettingRegistry],
  requires: [ISettingRegistry, ICommandPalette, IMainMenu],
  activate: (app: JupyterFrontEnd, settingRegistry: ISettingRegistry | null, palette: ICommandPalette, mainMenu: IMainMenu) => {
    const { commands } = app;
    eval('window.app = app');
    console.log('JupyterLab extension naasai is activated!');
    console.log(settingRegistry)
    console.log(palette)

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

    // Create a blank content widget inside of a MainAreaWidget
    const content = new Widget();
    const widget = new MainAreaWidget({ content });
    widget.id = 'naasai';
    widget.title.label = 'Naas manager';
    widget.title.closable = false;
      

    // Add an image element to the content
  let ifrm = document.createElement('iframe');
  content.node.appendChild(ifrm);
  ifrm.setAttribute('src', '/naas')
  ifrm.setAttribute('style', "width:100%;height:100%;")


    // Add an application command
    const command: string = 'naasai:open-manager';
    app.commands.addCommand(command, {
      label: 'Naas manager',
      execute: () => {
        if (!widget.isAttached) {
          // Attach the widget to the main work area if it's not there
          app.shell.add(widget, 'main' ,{
            'rank': -100000,
            'activate': false
          });
        } else {
          // Activate the widget
          app.shell.activateById(widget.id);
        }

      }
    });

    // Add the command to the palette.
    palette.addItem({ command, category: 'Naas manager' });
    
    const naasMenu = new Menu({ commands });

    naasMenu.title.label = 'Naas';
    mainMenu.addMenu(naasMenu, { rank: 1000 });
    naasMenu.addItem({ command });

    app.restored.then(() => {
      app.commands.execute(command);
    })

    app.started.then(function() {})

  }
};

export default plugin;
