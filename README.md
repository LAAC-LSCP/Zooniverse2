# Zooniverse2

Split audios in chunks and uploads them to zooniverse

## Usage

```
zooniverse.py [-h] --project-slug PROJECT_SLUG --subject-set
                     SUBJECT_SET --sample-size SAMPLE_SIZE --zooniverse-login
                     ZOONIVERSE_LOGIN --zooniverse-pwd ZOONIVERSE_PWD
                     [--threads THREADS]
                     [--target-speaker-type {CHI,OCH,FEM,MAL}]
                     path
```

<table>
<tr>
    <th>argument</th>
    <th>description</th>
    <th>default value</th>
</tr>
<tr>
    <td>project-slug</td>
    <td>project slug (e.g.: lucasgautheron/my-new-project)</td>
    <td></td>
</tr>
<tr>
    <td>subject-set</td>
    <td>prefix for the subject set</td>
    <td></td>
</tr>
<tr>
    <td>sample-size</td>
    <td>how many vocalization events per recording</td>
    <td></td>
</tr>
<tr>
    <td>target-speaker-type</td>
    <td>speaker type to get chunks from</td>
    <td>CHI</td>
</tr>
<tr>
    <td>zooniverse-login</td>
    <td>zooniverse login</td>
    <td></td>
</tr>
<tr>
    <td>zooniverse-pwd</td>
    <td>zooniverse password</td>
    <td></td>
</tr>
<tr>
    <td>threads</td>
    <td>how many threads to perform the conversion on</td>
    <td></td>
</tr>
</table>