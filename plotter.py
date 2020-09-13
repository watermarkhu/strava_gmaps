from IPython.display import display
import ipywidgets as widgets
import gmaps


class PlotApp(object):

    def __init__(self, api_key, df, categories:list, max_intensity:int=800, point_radius:int=5):
        """
        Jupyter widget for exploring KFC and Starbucks outlets

        Using checkboxes, the user chooses whether to include
        Starbucks, KFC outlets, both or neither.
        """
        gmaps.configure(api_key=api_key)

        if type(categories) == str:
            categories = [categories]
        self.max_intensity = max_intensity
        self.point_radius = point_radius
        self._df = df
        self._categories = categories
        self._catoptions = {cat: list(set(self._df.loc[:, cat])) for cat in categories}
        self._checkboxes = None
        self._mislider = None
        self._prslider = None
        self.heatmap = None


        title_widget = widgets.HTML(
            '<h3>Explore GPX and TCX data</h3>'
        )
        boxes = self._render_controls()
        map_figure = self._render_map()

        self._container = widgets.VBox(
            [title_widget, *boxes, map_figure])
        

    def render(self):
        """ Render the widget """
        display(self._container)

    def _render_map(self):
        """ Render the initial map """
        fig = gmaps.figure()
        self.heatmap = gmaps.heatmap_layer(
            self._df[['latitude', 'longitude']],
            max_intensity = self.max_intensity,
            point_radius = self.point_radius
        )
        fig.add_layer(self.heatmap)
        self.heatmap.max_intensity = self.max_intensity
        self.heatmap.point_radius = self.point_radius
        self.fig = fig
        self.gradient = self.heatmap.gradient
        return fig

    def _render_controls(self, *args, **kwargs):

        boxes = []

        self._mislider = widgets.IntSlider(
            value=self.max_intensity,
            min=1,
            max=1000,
            description='Max Intensity',
            continuous_update=False
        )
        self._mislider.observe(self._on_mi_change, names='value')
        self._prslider = widgets.IntSlider(
            value=self.point_radius,
            min=1,
            max=50,
            description='Point Radius',
            continuous_update=False
        )
        self._prslider.observe(self._on_pr_change, names='value')
        boxes.append(widgets.VBox([
            self._mislider,
            self._prslider
        ]))

        """ Render the checkboxes """
        self._checkboxes = {}
        
        for category in self._categories:
            self._checkboxes[category] = {}
            for option in self._catoptions[category]:
                checkbox = widgets.Checkbox(
                    value=True,
                    description=option
                )
                checkbox.observe(self._on_checkbox_change, names='value')
                self._checkboxes[category][option] = checkbox
            boxes.append(widgets.HTML(
                '<h4>{}</h4>'.format(category)
            ))
            boxes.append(widgets.Box(
                list(self._checkboxes[category].values()),
                layout=widgets.Layout(flex_flow='row wrap')
            ))
        return boxes

    def _on_mi_change(self, change):
        self.heatmap.max_intensity = self._mislider.value

    def _on_pr_change(self, change):
        self.heatmap.point_radius = self._prslider.value

    def _on_checkbox_change(self, change):
        """
        Called when the checkboxes change

        This method builds the list of symbols to include on the map,
        based on the current checkbox values. It then updates the
        symbol layer with the new symbol list.
        """
        in_cat_selected = []
        for category, catoptions in self._checkboxes.items():
            selected = [option for option, checkbox in catoptions.items() if checkbox.value]
            in_cat_selected.append(self._df[category].isin(selected))

        locations = self._df.loc[[all([*checks]) for checks in zip(*in_cat_selected)], ['latitude', 'longitude']]
        self.heatmap.locations = locations
        return self._container
