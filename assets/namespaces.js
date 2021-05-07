// require('./style.css')

// region Leaflet extensions

L.DivIcon.Scatter = L.DivIcon.extend({
    createIcon: function(oldIcon) {
           let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
           icon.style.backgroundColor = this.options.color;
           return icon;
    }
})

L.divIcon.scatter = function(opts) {
    return new L.DivIcon.Scatter(opts);
}

// endregion

function resolve(primary, fallback, keys){
    const obj = {}
    for(let i = 0; i < keys.length; i++){
        obj[keys[i]] = (primary && primary[keys[i]])? primary[keys[i]] : fallback[keys[i]]
    }
    return obj
}

// region Color

const colorDefaults = {min:0, max:1, colorscale:['yellow', 'red', 'black']}

function getColorContinuous(options, value){
    const {min, max, colorscale} = resolve(options, colorDefaults, ["min", "max", "colorscale"])
    const csc = chroma.scale(colorscale).domain([min, max])
    return csc(value)
}

function getColorDiscrete(options, value) {
    const {classes, colorscale} = resolve(options, colorDefaults, ["classes", "colorscale"])
    let color = null;
    for (let i = 0; i < classes.length; ++i) {
        if (value > classes[i]) {
            color = colorscale[i]
        }
    }
    return color
}

function getColor(options, value){
    const {classes} = resolve(options, colorDefaults, ["classes"])
    if(classes){
        return getColorDiscrete(options, value)
    }
    return getColorContinuous(options, value)
}

// endregion

const scatterDefaults = {colorProp: "value", circleOptions: {fillOpacity:1, stroke:false, radius:8}};

window.myNamespace = Object.assign({}, window.myNamespace, {
    mySubNamespace: {
        pointToLayer: function(feature, latlng, context){
            const {circleOptions, colorProp} = resolve(context.props.hideout, scatterDefaults,
                ["circleOptions", "colorProp"])
            if (typeof feature.properties[colorProp] !== 'undefined')
            {
                label = String(feature.properties[colorProp].toFixed(0))
                const icon = L.divIcon.scatter({
                    html: '<div><span>' + label + '</span></div>',
                    iconSize: L.point(20, 20),
                    className: "marker-modified",
                    color: getColor(context.props.hideout, feature.properties[colorProp])
                });
                return L.marker(latlng, {icon : icon})
            }
        },

        clusterToLayer: function (feature, latlng, index, context) {
            const {circleOptions, colorProp} = resolve(context.props.hideout, scatterDefaults,
                ["circleOptions", "colorProp"])
            const leaves = index.getLeaves(feature.properties.cluster_id);
            // Choose just one value to be representative
            leave = leaves[0]
            if (typeof leave.properties[colorProp] !== 'undefined')
            {
                label = String(leave.properties[colorProp].toFixed(0))
                const icon = L.divIcon.scatter({
                    html: '<div><span>' + label + '</span></div>',
                    iconSize: L.point(20, 20),
                    className: "marker-modified",
                    color: getColor(context.props.hideout, leave.properties[colorProp])
                });
                return L.marker(latlng, {icon : icon})
            }

        }

    },
});