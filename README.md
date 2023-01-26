<p align="center"><img alt="Naas Logo" src="https://i.imgur.com/ZpcvnKi.jpg")
"></p>



## :sparkles: Welcome to Naas!

Notebooks as a service (Naas) is an open source platform that allows anyone touching data (business analysts, scientists and engineers) to create powerful data engines combining automation, analytics and AI from the comfort of their Jupyter notebooks.

Naas is an attempt to propose an alternative to Google Colab, powered by the community.

In addition to Google Colab, Naas platform upgrade notebooks with with 3 low-code layers: features, drivers, templates.

- **Templates** enable the user to create automated data jobs and reports in minutes.
- **Drivers** act as connectors to push and/or pull data from databases, APIs, and Machine Learning algorithms and more.
- **Features** transform Jupyter in a production ready environment with scheduling, asset sharing, and notifications.



## 🚀 Quick Start

Try all of Naas's features for free using -- [Naas cloud](https://app.naas.ai/hub/login) -- a stable environment, without having to install anything.

    
## ⚙️ Installation
    
Check out our step by step guide on how to [set up Naas locally.](https://docs.naas.ai/install-locally#run-locally)

<!-- ## ⚙️ Installation

### Install only Naas

`pip3 install naas`

### Install Naas with drivers

`pip3 install 'naas[full]'`

## :hourglass: Run locally

### Requirements

- Docker
- Make (Not needed on windows and not needed on Linux/MacOS if you prefer to use `docker-compose` directly).

### Run

**Linux / MacOS**

```bash
make
```

Then you can go on http://localhost:8888/lab?token=naas

**Windows**

You just need to double click on the file `windows_start.bat`, this will open a terminal, start naas and open your browser on http://localhost:8888/lab?token=naas.

## 🛑 Stop

**Linux / MacOS**

```bash
make stop
```
or if you want to delete the container as well you can run

```bash
make down
```

**Windows**

Double click on `windows_stop.bat`

## 📦 Build

You don't really have to run this, unless you changed something related to the `Dockerfile.dev`. The build process is done automatically when running naas (`make` or `make run`) if it never happened before.

**Linux / MacOS**

```bash
make build
```

### Open a shell in the container (root)

**Linux / MacOS**

```bash
make sh
```

### File structure for local development

When you land in your freshly started naas, on the left you should see a file structure like this:

```
.
├── awesome-notebooks
├── file_sharing
├── drivers
├── naas
└── Welcome_to_Naas.ipynb
```

When naas is starting, it will automatically mount `../drivers` and `../awesome-notebooks` in your home directory of your naas. This means that if these directories does not exists on your machine it will create them and `git clone` [naas drivers](https://github.com/jupyter-naas/drivers) in `../drivers` and [awesome-notebooks](https://github.com/jupyter-naas/awesome-notebooks) in `../awesome-notebooks`.

`naas` folder corespond to `.` directory on your machine (where naas project is cloned).

`file_sharing` directory  is a folder created next to `./naas` to allow easy file sharing between your computer and naas container. Every file that you will drop in this directory, either from naas or from your computer will be accesible on both naas and your machine.

`Welcome_to_Naas.ipynb` is our welcoming notebook to get you a place to start your journey.

### Api documentation

We have a WIP documentation in swagger.

`http://127.0.0.1:5000/swagger/`

### Live reload 

If you do change in naas code, the server will live reload.

If you use naas in a notebook restart the kernel to get the changes.

### Naas Manager
Open Naas manager outsite of jupyter context :

`http://localhost:5000/naas`

## Run test 

Open Jupyterlab
click on `+` to open Launcher
Open Shell
Go the right directory `cd naas`
Run it in the shell `pytest -x`  to test your code

Each Change you do from your IDE or from jupyter in the Naas folder is live reloaded
If you test naas feature inside a notebook reload your kernel between changes.
Same for the manager page you have to reload the Page to see the changes.
To go faster you can use `isolated Manager` to reload only manager and not full jupyterlab

## Check lint

`python -m black naas` format better
`python -m flake8 naas` check if any left error

## Publish

You can commit from jupyter or from your local IDE, code of Naas is sync between docker machine and your computer

this auto publish by github action on main branch -->


## ❤️ Contributing

We value all kinds of contributions - not just code. We are paticularly motivated to support new contributors and people who are looking to learn and develop their skills.


Please read our [contibuting guidelines](https://docs.naas.ai/contributing-to-naas) on how to get started.


## 🤔 Community Support

The naas [documentation](https://docs.naas.ai/) is a great place to start and to get answers for general questions.

- [Slack](https://join.slack.com/t/naas-club/shared_invite/zt-1970s5rie-dXXkigAdEJYc~LPdQIEaLA) (Live Discussions)
- [GitHub Issues](https://github.com/jupyter-naas/naas/issues/new) (Report Bugs)
- [GitHub Discussions](https://github.com/jupyter-naas/naas/discussions) (Questions, Feature Requests)
- [Twitter](https://twitter.com/JupyterNaas) (Latest News)
- [YouTube](https://www.youtube.com/c/naas-ai) (Video Tutorials)
- [Previous Community calls](https://naas-official.notion.site/3450f449df704f008c82004fd61f69ce?v=059be6a284e740e5b1013a57812a17f0) (Video call discussions with the naas team & other contributors.)
- [Naas's community page](https://www.notion.so/naas-official/Naas-Official-8150e2c35f9248049c48d3fe021b49bb) (To know more)

## :page_with_curl: License

The project is licensed under  [AGPL-3.0](https://opensource.org/licenses/AGPL-3.0)

<!-- ## Supporters: 
<p>
  <a href="http://sentry.com" title="Redirect to Sentry">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/sentry.svg" alt="Sentry" />
  </a>
  <a href="https://gitbook.com" title="Redirect to Gitbook">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/gitbook.svg" alt="Gitbooks" />
  </a>
</p>

**Authors:** [Jeremy Ravenel](https://github.com/jravenel), [Maxime Jublou](https://github.com/Dr0p42), [Martin Donadieu](https://github.com/riderx) -->
