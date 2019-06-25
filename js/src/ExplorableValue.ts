/* import {
    CoreDescriptionModel
} from './widget_core'; */

/* import {
    DescriptionView
} from './widget_description'; */

import {
    HTMLModel, HTMLView
} from '@jupyter-widgets/controls';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';


export
class ExplorableValueModel extends HTMLModel {
  defaults() {
    return {...super.defaults(),
      _model_name: ExplorableValueModel.model_name,
      _model_module: ExplorableValueModel.model_module,
      _model_module_version: ExplorableValueModel.model_module_version,
      _view_name: ExplorableValueModel.view_name,
      _view_module: ExplorableValueModel.view_module,
      _view_module_version: ExplorableValueModel.view_module_version,
      value : 'Hello World'
    };
  }

/*  static serializers: ISerializers = {
      ...DOMWidgetModel.serializers,
      // Add any extra serializers here
    }*/

  static model_name = 'ExplorableValueModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'ExplorableValueView';
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;
}

export
class ExplorableValueView extends HTMLView {
    /**
     * Called when view is rendered.
     */
    render() {
        super.render();
        this.content.classList.add('sage-explorable');
    }

    events() {
	return {'click': '_handle_click'};
    }

    /**
     * Handles when the button is clicked.
     */
    _handle_click(event: MouseEvent) {
        event.preventDefault();
        this.send({event: 'click'});
    }
}
