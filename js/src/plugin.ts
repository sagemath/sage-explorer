// Copyright (c) Odile Bénassy, Nathan Carter, Nicolas Thiéry
// Distributed under the terms of the GPLv2+.

import {
  Application, IPlugin
} from '@phosphor/application';

import {
  Widget
} from '@phosphor/widgets';

import {
  IJupyterWidgetRegistry
 } from '@jupyter-widgets/base';

import * as widgetExports from './ExplorableValue';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';

const EXTENSION_ID = 'new-sage-explorer:plugin';

/**
 * The explorable value plugin.
 */
const newSageExplorerPlugin: IPlugin<Application<Widget>, void> = {
  id: EXTENSION_ID,
  requires: [IJupyterWidgetRegistry],
  activate: activateWidgetExtension,
  autoStart: true
};

export default newSageExplorerPlugin;


/**
 * Activate the widget extension.
 */
function activateWidgetExtension(app: Application<Widget>, registry: IJupyterWidgetRegistry): void {
  registry.registerWidget({
    name: MODULE_NAME,
    version: MODULE_VERSION,
    exports: widgetExports,
  });
}
