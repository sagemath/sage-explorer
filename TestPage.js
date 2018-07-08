var MyHTMLModel = /** @class */ (function (_super) {
    __extends(MyHTMLModel, _super);
    function MyHTMLModel() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    MyHTMLModel.prototype.defaults = function () {
        return _.extend(_super.prototype.defaults.call(this), {
            _view_name: 'HTMLView',
            _model_name: 'MyHTMLModel'
        });
    };
    return MyHTMLModel;
}(HTMLModel));
//model = MyHTMLModel()
//exports.MyHTMLModel = MyHTMLModel;

var MyHTMLView = /** @class */ (function (_super) {
    __extends(MyHTMLView, _super);
    function MyHTMLView() {
        return _super !== null && _super.apply(this, arguments) || this;
    }

    MyHTMLView.prototype.events = function () {
        return {
            // Dictionary of events and their handlers.
            'click': '_handle_click'
        };
    };
    /**
     * Handles and validates user input.
     *
     * Calling model.set will trigger all of the other views of the
     * model to update.
     */
    MyHTMLView.prototype._handle_click = function (event) {
        event.preventDefault();
        var selected_link = this.model.get('selected_link');
        this.model.set('selected_link', !value, { updated_view: this });
        this.touch();
    };
    return MyHTMLView;
}(HTMLView));
