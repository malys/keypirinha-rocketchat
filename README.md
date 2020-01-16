<p align="center">
  <img src="https://github.com/RocketChat/Rocket.Chat.Artwork/raw/master/Logos/icon-1024.png" width="100" height="100" />
</p>

# Keypirinha Plugin: RocketChat

This is RocketChat, a plugin for the
[Keypirinha](http://keypirinha.com) launcher.

![Demo](usage.gif)

## Download

https://github.com/malys/keypirinha-rocketchat/releases


## Install

#### Managed

[@ueffel](https://github.com/ueffel) wrote [PackageControl](https://github.com/ueffel/Keypirinha-PackageControl), a package manager that eases the install of third-party packages.
It must be installed manually.

#### Manual

Once the `Rocketchat.keypirinha-package` file is installed,
move it to the `InstalledPackage` folder located at:

* `Keypirinha\portable\Profile\InstalledPackages` in **Portable mode**
* **Or** `%APPDATA%\Keypirinha\InstalledPackages` in **Installed mode** (the
  final path would look like
  `C:\Users\%USERNAME%\AppData\Roaming\Keypirinha\InstalledPackages`)

#### Configuration

```ini
[main]
AUTH = "auth"       <- In your personal profile (My Account), Generate a Personal Access Tokens for this use and add it "AUTH" field.
USER_ID = "id"      <- RC UserId
DOMAIN = "https://open.rocket.chat" <- domain of RC host
```

## Usage

Open Keypirinha and type 'rocketchat'. Once the suggestion appears press TAB or ENTER to open all suggestions.

## Change Log

### 0.1.0
* Send message from keypirinha
* Open browser only mode

### 0.0.1-beta-x
* Released Beta version

## TODO

* User refresh improvements
* Send message from keypirinha
* Create generic extension to consume easily API rest


## License

This package is distributed under the terms of the MIT license.

## Credits
[@Fuhrmann](https://github.com/Fuhrmann), developer of [keypirinha-gitmoji](https://github.com/Fuhrmann/keypirinha-gitmoji/blob/master/README.md)

