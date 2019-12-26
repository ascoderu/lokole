import React from 'react';
import { Form, Icon, Input, Button } from 'antd';
import axios from 'axios';

const githubApi = axios.create({ baseURL: 'https://api.github.com' });

class SettingsForm extends React.Component {
  _validateGithubAccessToken = async (_rule, value, callback) => {
    const { setFieldsValue } = this.props.form;

    if (!value) {
      setFieldsValue({
        githubUsername: undefined,
        githubAvatarUrl: undefined,
      }, callback);
      return;
    }

    try {
      const response = await githubApi.get('/user', {
        headers: { Authorization: `Token ${value}` }
      })
      setFieldsValue({
        githubUsername: response.data.login,
        githubAvatarUrl: response.data.avatar_url,
      }, callback);
    } catch (error) {
      callback(error.response.data.message);
      return;
    }
  };

  handleSubmit = e => {
    e.preventDefault();

    this.props.form.validateFields((err, values) => {
      if (!err) {
        this.props.onChange(values);
      }
    });
  };

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit}>
        <Form.Item>
          {getFieldDecorator('serverEndpoint', {
            rules: [{ required: true, message: 'Please input the server endpoint!' }],
            initialValue: this.props.initialValue.serverEndpoint || 'https://mailserver.lokole.ca',
          })(
            <Input
              prefix={<Icon type="api" style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="Enter server endpoint"
            />,
          )}
        </Form.Item>
        <Form.Item>
          {getFieldDecorator('githubAccessToken', {
            rules: [{ validator: this._validateGithubAccessToken }],
            initialValue: this.props.initialValue.githubAccessToken,
          })(
            <Input.Password
              prefix={<Icon type="github" style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="Enter Github access token"
            />,
          )}
        </Form.Item>
        <Form.Item style={{display: 'none' }}>
          {getFieldDecorator('githubUsername', {
            initialValue: this.props.initialValue.githubUsername,
          })(
            <Input readOnly hidden />,
          )}
        </Form.Item>
        <Form.Item style={{display: 'none' }}>
          {getFieldDecorator('githubAvatarUrl', {
            initialValue: this.props.initialValue.githubAvatarUrl,
          })(
            <Input readOnly hidden />,
          )}
        </Form.Item>
        <Form.Item>
        <Button type="primary" htmlType="submit">
          Save settings
        </Button>
        </Form.Item>
      </Form>
    );
  }
}

export default Form.create({ name: 'settings' })(SettingsForm);
