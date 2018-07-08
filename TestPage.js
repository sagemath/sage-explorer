var NavHTMLModel = /** @class */ (function (_super) {
    __extends(NavHTMLModel, _super);
    function NavHTMLModel() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    NavHTMLModel.prototype.defaults = function () {
        return _.extend(_super.prototype.defaults.call(this), {
            _view_name: 'NavHTMLView',
            _model_name: 'NavHTMLModel'
        });
    };
    return NavHTMLModel;
}(HTMLModel));
//model = MyHTMLModel()
//exports.MyHTMLModel = MyHTMLModel;

var NavHTMLView = /** @class */ (function (_super) {
    __extends(NavHTMLView, _super);
    function NavHTMLView() {
        return _super !== null && _super.apply(this, arguments) || this;
    }

    NavHTMLView.prototype.events = function () {
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
    NavHTMLView.prototype._handle_click = function (event) {
        event.preventDefault();
        var selected_link = this.model.get('selected_link');
        this.model.set('selected_link', !value, { updated_view: this });
        this.touch();
    };
    return NavHTMLView;
}(HTMLView));
