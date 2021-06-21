#pragma once

#include "binaryninjaapi.h"
#include "uicontext.h"
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QTextEdit>
#include <vector>

class BINARYNINJAUIAPI FormInputDialog : public QDialog
{
	Q_OBJECT

	std::vector<BinaryNinja::FormInputField>* m_fields;
	std::vector<QWidget*> m_fieldControls;

	void openFileName(QLineEdit* edit, const std::string& ext);
	void saveFileName(QLineEdit* edit, const std::string& ext, const std::string& defaultName);
	void directoryName(QLineEdit* edit, const std::string& defaultName);

 public:
	FormInputDialog(
	    QWidget* parent, std::vector<BinaryNinja::FormInputField>* fields, const std::string& title);

 protected Q_SLOTS:
	void finish();
};
