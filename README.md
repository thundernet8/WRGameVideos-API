## WRGameVideos-API

Supply most model data via RESTFUL API, only JSON supported

## Third App

* register url - yourapidomain.com//apps/register (need login first)
* app review - yourapidomain.com/apps/<int:appid>/review (only administrator can approve a app)
* app list - yourapidomain.com/apps
* app detail - yourapidomain.com/apps/<int:appid> (you can find ==App Key== and ==App Secret== here)

## API request

### request access_token

* request url - yourapidomain.com/open/v1.0/access_token (GET method)
* url parameters
** grant_type - 'authorization_code'
** client_id - your app key
** tstrap - timestrap now (UTC+0)
** redirect_uri - callback url, must same as the redirect url provided when registered the app
** sign - a hmac hash string of 'app key+timestrap+redirect url', using App Secret as encrypt key

if everything is ok, return a json string including access_token:
```
{
  "error": "ab891e*************d20", 
  "expiration": 3600
}
```

or return kinds of errors like:
```
{
  "error": "incorrect_sign", 
  "message": "signature error"
}
```

### request API using access_token

before API request, access_token will be verified, if an error occured, it will return:

```
{
  "error": "unauthorized", 
  "message": "Invalid access_token", 
  "request_token": "yourapidomain/open/v1.0/access_token"
}
```
you can forward to the value of `request_token` which is a url to request a access_token

a successful API request result is based on the specified API
