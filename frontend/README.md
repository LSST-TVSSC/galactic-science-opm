# Frontend code

Some of the frontend code in this repo is written in here. For now, it is 
mostly UI components, but more might follow in the future.

The components are based on [lit](https://lit.dev/), which are pretty much
web components. 

The components are written in typescript.

## Requirements

- NodeJS
- NPM

## Setup

1. Open your terminal in this folder (frontend)
2. Run `npm install`: This installs all the needed packages.


## Development

The setup here works well with this docker command for the backend (Django):
`docker compose -f compose.base.yaml -f compose.local.yaml up -d`

Run `npx vite build --watch` to start vite in watch-mode. This re-runs the build
on file changes. Then just reload the page to see your code changes.

### Workflow for a new component

1. Look at the other components and copy the folder and change the names accordingly.
    Heads-Up: custom elements need to have tag names like this, e.g. `<astro-element>`.
    Single word elements are not valid. 
2.  Create an entry point for your component. In the component based approach used
    so far, this will mostly be an import to your tag definition (see other entry points 
    in ./src/pages).  

    For example, if you want to add a component to the home page, you might
    create a new file in src/pages called `home.ts`. In that file, you might put something 
    this:

    ```js
    import "../components/astro-element/astro-element"
    ```
3.  Add the entrypoint to `vite.config.ts` under `input`, e.g.:
    ```js
    // ...
    input: {
            target_detail: "src/pages/target-detail.ts",
            target_list: "src/pages/target-list.ts",
            observations: "src/pages/observations.ts",
            home: "src/pages/home.ts",
        },
    // ...
    ```
4.  Add the Django tag `vite_asset` to the page(s) where you want to include your new 
    component, e.g.:
    ```html
    {% load vite %}
    <!-- other stuff... --> 
    <script type="module" src="{% vite_asset 'src/pages/home.ts' %}"></script>
    ```

## Build / Deployment

There is a stage in the Dockerfile that builds the frontend code and moves it
to the static directory of Django.

The assets are included using a tag in django called `vite_asset`. 
This means that the files written here have to be specifically included on the pages
where they are needed. This has the advantage, that we don't have to serve huge 
files like libraries with every request, even if they are not needed for that 
particular page.


